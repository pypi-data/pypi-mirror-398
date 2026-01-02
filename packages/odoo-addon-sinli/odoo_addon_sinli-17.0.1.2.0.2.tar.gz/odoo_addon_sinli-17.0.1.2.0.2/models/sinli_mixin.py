from odoo import _, fields, models
from odoo.exceptions import ValidationError
from sinli.common.encoded_values import OrderType
from sinli import Document
from sinli.doctype import DocumentType
import re, base64
from datetime import datetime, time
from markupsafe import Markup
import logging
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class SinliImportMixin(models.AbstractModel):
    """Mixin for shared SINLI import functionalities"""
    _name = 'sinli.import.mixin'
    _description = 'SINLI Import Mixin'
    
    def _get_sinli_message(self, sinli_content):
        decoded_bytes = base64.b64decode(sinli_content)
        decoded_message = decoded_bytes.decode('windows-1252')
        sinli_message = Document.from_str(decoded_message)
        return sinli_message
    
    def _generate_sinli_attachment(self):
        # Create an attachment from the message body
        body_content = self.message_ids.sorted('id')[:1].body
        soup = BeautifulSoup(body_content, 'html.parser')
        sinli_text = soup.get_text()

        content_bytes = sinli_text.encode('windows-1252', errors='ignore')
        datas_bytes = base64.b64encode(content_bytes)
        datas_str = datas_bytes.decode('ascii')

        attachment = self.env['ir.attachment'].create({
            'name': 'sinli_message_{}.txt'.format(self.id),
            'datas': datas_str,
            'res_model': 'sinli.message',
            'res_id': self.id,
        })
        self.sinli_attachment = attachment.id

    def _find_partner_by_sinli_id(self, sinli_id):
        sender = self.env['res.partner'].search([('sinli_id', '=', sinli_id)], limit=1)
        if not sender:
            raise ValidationError(
                _("No partner found with SINLI ID: %s. Please create a partner with this Sinli ID.") % sinli_id
            )
        return sender
    
    def _validate_sinli_ids(self, sinli_message, sender):
        _logger.info("Validating SINLI IDs for message: %s", sinli_message.long_id_line)
        _logger.info("Sender SINLI ID: %s, Email: %s", sender.sinli_id, sender.sinli_email)
        _logger.info("Company SINLI ID: %s", self.env.company.partner_id.sinli_id)
        _logger.info("Message SINLI IDs - FROM: %s, TO: %s",
                     sinli_message.long_id_line.FROM, sinli_message.long_id_line.TO)
        if not (sinli_message.long_id_line.FROM):
            return _("The message does not have SINLI ID for receiver/sender.")
        
        if sinli_message.long_id_line.FROM != sender.sinli_id:
            return _("Sender's SINLI ID (%s) does not match the SINLI ID for %s.") % (
                sinli_message.long_id_line.FROM, sender.sinli_email
            )
        
        # if sinli_message.long_id_line.TO != self.env.company.partner_id.sinli_id:
        #     return _("Receiver SINLI ID (%s) does not match the company's SINLI ID.") % (
        #         sinli_message.long_id_line.TO
        #     )
        return None
    
    def _find_product_by_isbn(self, isbn):
        formatted_isbn = re.sub(r"[-\s]", "", isbn)
        self.env.cr.execute("""
            SELECT id FROM product_template
            WHERE REGEXP_REPLACE(isbn_number, '[-\\s]', '', 'g') = %s
            LIMIT 1
        """, (formatted_isbn,))
        
        result = self.env.cr.fetchone()
        return self.env['product.template'].browse(result[0]) if result else None
    
    def _get_pricelist_id(self, sender, line):
        if (not hasattr(line, 'ORDER_TYPE') or 
            not line.ORDER_TYPE or
            (sender.property_product_pricelist.is_deposit_pricelist() == 
             (line.ORDER_TYPE == OrderType.DEPOSIT))):
            return sender.property_product_pricelist.id
        
        pricelist_mapping = {
            OrderType.FIRM: self.env.company.default_pricelist_firm_sale.id,
            OrderType.DEPOSIT: self.env.company.default_pricelist_deposit_sale.id,
            OrderType.FAIRE: self.env.company.default_pricelist_fair_sale.id,
            OrderType.OTHER: self.env.company.default_pricelist_other_sale.id,
        }
        return pricelist_mapping.get(line.ORDER_TYPE)
    
    def _process_order_date(self, line):
        if hasattr(line, 'ORDER_DATE') and line.ORDER_DATE:
            date = fields.Date.from_string(line.ORDER_DATE)
            date_and_time = datetime.combine(date, time())
            return fields.Datetime.to_string(date_and_time)
        return fields.Datetime.now()
    
    def _mark_message_as_imported(self, order):
        self.generated_document = order
        self.imported = True
        self.import_date = fields.Datetime.now()
        self.import_user = self.env.user.id
    
    def _import_purchase_order(self, sinli_message, sender):
        """Import a purchase order from a SINLI message
        Args:
            sinli_message: Parsed SINLI document
            sender: Partner sending the order
        Returns:
            tuple: (result_message, purchase_order) or just error_message
        """

        if sinli_message.long_id_line.DOCTYPE != DocumentType.ENVIO.name:
            return _("The document type is not 'ENVIO', cannot import as a purchase order.")
        
        order_lines = []
        not_imported_products = []
        date_order = fields.Datetime.now()
        
        for line in sinli_message.doc_lines:
            if line.TYPE == "D":  # Purchase Order line
                product = self._find_product_by_isbn(line.ISBN)

                # Set price with or without VAT based on company settings
                if self.env.company.account_purchase_tax_id.price_include:
                    product_price = line.PRICE_W_VAT
                else:
                    product_price = line.PRICE_NO_VAT

                if product:
                    order_lines.append((0, 0, {
                        'product_id': product.product_variant_ids[0].id,
                        'product_qty': line.AMOUNT,
                        'product_barcode': product.barcode,
                        'price_unit': product_price,
                    }))
                else:
                    not_imported_products.append(line.TITLE)
            
            elif line.TYPE == "C":  # Purchase Order header
                date_order = self._process_order_date(line)

        # If there are products that could not be imported, return error message
        if not_imported_products:
            message = _("Order not imported. Before importing you need to create the following books:\n%s") % (
                "\n".join(not_imported_products))
            return message
                        
        # Create purchase order
        purchase_order = self.env['purchase.order'].create({
            'partner_id': sender.id,
            'date_order': date_order,
            'order_line': order_lines,
        })
        
        if not purchase_order:
            return _("There was an error importing the order")
        
        sinli_reference_message = Markup(
            "Pedido creado a partir de la importación de un mensaje SINLI:"
            " <a href=# data-oe-model='{model}' data-oe-id='{id}'>{id}</a>"
        ).format(model=self._name, id=self.id)
        purchase_order.message_post(body=sinli_reference_message)
        
        message = _("Order imported successfully: %s") % purchase_order.name
        return message, purchase_order
    
    def _import_sale_order(self, sinli_message, sender):
        """Import a sale order from a SINLI message
        Args:
            sinli_message: Parsed SINLI document
            sender: Partner sending the order
        Returns:
            tuple: (result_message, sale_order) or just error_message
        """

        if sinli_message.long_id_line.DOCTYPE != DocumentType.PEDIDO.name:
            return _("The document type is not 'PEDIDO', cannot import as a sale order.")
        
        order_lines = []
        not_imported_products = []
        date_order = fields.Datetime.now()
        pricelist_id = None
        
        for line in sinli_message.doc_lines:
            if line.TYPE == "D":  # Sale Order line
                product = self._find_product_by_isbn(line.ISBN)
                if product:
                    order_lines.append((0, 0, {
                        'product_id': product.product_variant_ids[0].id,
                        'product_uom_qty': line.QUANTITY,
                        'price_unit': line.PRICE,
                    }))
                else:
                    not_imported_products.append(line.TITLE)
            
            elif line.TYPE == "C":  # Sale Order header
                date_order = self._process_order_date(line)
                pricelist_id = self._get_pricelist_id(sender, line)
                
                if not pricelist_id:
                    return False, _("Please config the default pricelist for each type of sale order in the company settings.")
        
        # Create sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': sender.id,
            'date_order': date_order,
            'order_line': order_lines,
            'pricelist_id': pricelist_id
        })
        
        if not sale_order:
            return _("There was an error importing the order")
        
        sinli_reference_message = Markup(
            "Pedido creado a partir de la importación de un mensaje SINLI:"
            " <a href=# data-oe-model='{model}' data-oe-id='{id}'>{id}</a>"
        ).format(model=self._name, id=self.id)
        sale_order.message_post(body=sinli_reference_message)
        
        if not not_imported_products:
            message = _("Order imported successfully: %s") % sale_order.name
        else:
            message = _("Order imported successfully: %s. But the following products were not imported: \n %s") % (
                sale_order.name, "\n".join(not_imported_products)
            )
        
        return message, sale_order
    
    def _import_products(self, sinli_message, sender):
        imported_books = []
        not_imported_books = []
        
        for book_line in sinli_message.lines_by_type["Book"]:
            # Check if the book already exists
            if self._find_product_by_isbn(book_line.ISBN_INVOICE):
                not_imported_books.append(book_line.TITLE_FULL)
                continue
            
            # Create new book product
            isbn = re.sub(r"[-\s]", "", book_line.ISBN_INVOICE)
            new_book = self.env['product.template'].create({
                'name': book_line.TITLE_FULL,
                'type': "product",
                'categ_id': self.env.ref("gestion_editorial.product_category_books").id,
                'list_price': book_line.PRICE_PV,
                'isbn_number': isbn,
                'barcode': isbn,
                'purchase_ok': True,
                'sale_ok': True,
            })
            
            # Create supplier info for the book
            self.env['product.supplierinfo'].create({
                'product_tmpl_id': new_book.id,
                'partner_id': sender.id,
                'price': book_line.PRICE_PVP,
                'min_qty': 0
            })
            
            # Process authors
            if book_line.AUTHORS:
                author_type_id = self.env.ref('gestion_editorial.contact_type_author').id

                for author_name in book_line.AUTHORS.split(","):
                    author_contact = self.env['res.partner'].search([
                        ('name', '=ilike', author_name),
                        ('is_author', '=', True)
                    ], limit=1)
                    if not author_contact:
                        author_contact = self.env['res.partner'].create({
                            'name': author_name,
                            'is_author': True
                        })

                    new_authorship_vals = {
                        'author_id': author_contact.id,
                        'product_id': new_book.id,
                        'contact_type': author_type_id,
                        'sales_price': 0
                    }                    

                    self.env['authorship.product'].create(new_authorship_vals)
            
            imported_books.append(new_book.name)
        
        return _("Import complete. Books successfully imported: \n %s \nBooks that already exist and were not imported: \n %s") % (
            "\n".join(imported_books), "\n".join(not_imported_books)
        )