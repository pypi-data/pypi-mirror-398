from odoo import _, models
import base64
import re
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

# as per https://odoo-development.readthedocs.io/en/latest/dev/py/external-imports.html
try:
    from stdnum import isbn
    from sinli import *
except ImportError as err:
    _logger.error(err)


class SinliPurchaseOrder(models.Model):
    """ Extend purchase order for sinli management """
    _description = "Sinli Purchase Orders"
    _inherit = 'purchase.order'

    def action_sinli_export_purchase_order(self):

        if not self.env.company.partner_id.sinli_email:
            raise ValidationError(_("Sinli email is not set for this company."))
        elif not self.partner_id.sinli_email:
            raise ValidationError(_("Sinli email is not set for this contact."))

        purchase_order = pedido.v7.PedidoDoc()

        # Short_id_line
        purchase_order.short_id_line.FROM = self.env.company.partner_id.sinli_email
        purchase_order.short_id_line.TO = self.partner_id.sinli_email
        purchase_order.short_id_line.DOCTYPE = doctype.DocumentType.PEDIDO.name
        purchase_order.short_id_line.TYPE = "I"
        purchase_order.short_id_line.VERSION = "07"
        purchase_order.short_id_line.TRANSMISION_NUMBER = "0"   # ?????
        
        # Long_id_line
        purchase_order.long_id_line.FROM = self.env.company.partner_id.sinli_id
        purchase_order.long_id_line.TO = self.partner_id.sinli_id
        purchase_order.long_id_line.TYPE = "I"
        purchase_order.long_id_line.FORMAT = "N"
        purchase_order.long_id_line.DOCTYPE = doctype.DocumentType.PEDIDO.name
        purchase_order.long_id_line.FANDE = "FANDE"
        purchase_order.long_id_line.FORMAT = "N"
        purchase_order.long_id_line.VERSION = "07"

        # Header line
        header = pedido.v7.PedidoDoc.Header()
        header.TYPE = "C"
        header.PROVIDER = self.partner_id.name
        header.ORDER_DATE = self.date_order.strftime('%Y%m%d')
        header.CURRENCY = "E"
        header.MAX_DELIVERY_DATE = "19700101"
        header.ASKED_DELIVERY_DATE = "19700101"
        header.STRICT_MAX_DELIVERY_DATE = False
        header.ORDER_CODE = self.name

        if not self.env.company.stock_picking_type_compra_deposito_id.id:
            raise ValidationError(_("Deposit purchase picking type is not set. Configure it in company settings."))

        if self.picking_type_id.id == self.env.company.stock_picking_type_compra_deposito_id.id:
            header.ORDER_TYPE = "D" # Deposit purchase
        else:
            header.ORDER_TYPE = "F" # Firm purchase

        purchase_order.doc_lines.append(header)

        # Create one line for each product
        for line in self.order_line:
            # Check if product has ISBN
            formated_isbn = re.sub(r"[-\s]", "", line.product_barcode) if line.product_barcode else ""

            product = pedido.v7.PedidoDoc.Detail()
            product.TYPE = "D"
            product.ISBN = formated_isbn
            product.QUANTITY = int(line.product_qty)
            product.EAN = formated_isbn
            product.PRICE = line.price_unit
            product.TITLE = line.product_id.name
            product.ORDER_SOURCE = "N"
            product.EXPRESS = False
            product.ORDER_CODE = self.name
            product.INCLUDE_PENDING = True  # What is this?
            purchase_order.doc_lines.append(product)

        purchase_order.long_id_line.LEN = len(purchase_order.doc_lines) + 2     # Check if this works properly

        # Build a SINLI email subject
        subject = Subject()
        subject.FROM = self.env.company.partner_id.sinli_id
        subject.TO = self.partner_id.sinli_id
        subject.DOCTYPE = doctype.DocumentType.PEDIDO.name
        subject.VERSION = "07"

        # Create attachment
        file_name = f"SINLI_{doctype.DocumentType.PEDIDO.name}_{self.name}.txt"
        file_data = base64.b64encode(str.encode(str(purchase_order), "windows-1252"))

        ir_values = {
            "name": file_name,
            "type": "binary",
            "datas": file_data,
            "store_fname": file_name,
            "mimetype": "text/plain",
        }
        mail_attachment = self.env["ir.attachment"].create(ir_values)

        # Create email with the sinli file as attachment
        create_values = {
            "subject": str(subject),
            "email_to": self.partner_id.sinli_email,
            "email_from": self.env.company.partner_id.sinli_email,
            "recipient_ids": [self.partner_id.id],
            "reply_to": "",
            "model": self._name,
            "res_id": self.id,
            "attachment_ids": [mail_attachment.id]  # Include attachment ID
        }
        mail = self.env["mail.mail"].create(create_values)
        mail.send()
        print(f"*****************{mail.state}")

        if mail.state == "sent":
            dialog_message = _("Sinli email succesfully sent to %s") % self.partner_id.sinli_email

            # Add reference to purchase order notes
            sinli_reference_message = _(
                "SINLI export message sent: <a href=# data-oe-model='{model}' data-oe-id='{id}'>{id}</a>"
            ).format(
                model=mail._name,
                id=mail.id,
            )
            self.message_post(body=sinli_reference_message)
        else:
            dialog_message = _("Sinli email could not be sent. Error %s.") % mail.state
            
        sinli_dialog = self.env['sinli.dialog'].create({
            'message': dialog_message,
        })

        # Return dialog containing the information about the export proccess status
        return {
            'name': 'SINLI Export',
            'type': 'ir.actions.act_window',
            'res_model': 'sinli.dialog',
            'view_id': self.env.ref('sinli.sinli_dialog_view_form').id,
            'view_mode': 'form',
            'target': 'new',
            'res_id': sinli_dialog.id,
        }
