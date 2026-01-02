from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import base64
import datetime

import logging

_logger = logging.getLogger(__name__)

# as per https://odoo-development.readthedocs.io/en/latest/dev/py/external-imports.html
try:
    from stdnum import isbn
    from sinli import *
    from sinli.common import (
        SinliCode as c,
    )  # TODO: are these lines redundant and unnecessary?
    from sinli.subject import Subject
except ImportError as err:
    _logger.error(err)


class SinliExportWizard(models.TransientModel):
    _name = "sinli.export.wizard"
    _description = "Sinli Export Wizard"

    # document_type = fields.Selection(
    #     string="Document type",
    #     required=False,
    #     selection=[("libros", "LIBROS"), ("pedido", "PEDIDO")],
    #     compute='_compute_document_type'
    # )
    product_ids = fields.Many2many("product.template", string="Products", required=True)
    partner_ids = fields.Many2many(
        "res.partner",
        string="Contacto sinli",
        domain="[('sinli_email', '!=', None), ('sinli_id', '!=', None)]",
        required=True,
    )

    def export_catalogue_sinli(self):
        _logger.info(
            f"######## Wizard export catalogue: {len(self.product_ids)}"
        )

        # Check if the company speaks sinli
        if not self.env.company.partner_id.speak_sinli:
            raise ValidationError(
                "SINLI is not configured for the company, please go to configuration and complete the SINLI configuration.."
            )
        dialog_message = ""

        for partner in self.partner_ids:

            # Create a catalog documentn
            catalog = libros.v9.LibrosDoc()

            # sinli id and email from the company using odoo
            catalog.long_id_line.FROM = self.env.company.partner_id.sinli_id
            catalog.short_id_line.FROM = self.env.company.partner_id.sinli_email

            catalog.short_id_line.DOCTYPE = doctype.DocumentType.LIBROS.name
            catalog.long_id_line.DOCTYPE = doctype.DocumentType.LIBROS.name

            # sinli id and email of the selected contacts
            catalog.long_id_line.TO = partner.sinli_id
            catalog.short_id_line.TO = partner.sinli_email

            # Create the header line of the doc
            header = libros.v9.LibrosDoc.Header()
            header.TYPE = "C"
            header.PROVIDER = self.env.company.display_name
            header.CURRENCY = "E"

            catalog.doc_lines.append(header)

            for prod in self.product_ids:
                # Create authors list
                author_names = [author.name for author in prod.author_name]
                authors_string = ','.join(author_names) 

                # Create one book for the catalog document
                book = libros.v9.LibrosDoc.Book()
                book.EAN = prod.barcode
                book.ISBN_INVOICE = (
                    isbn.format(prod.isbn_number) if prod.isbn_number else ""
                )
                book.AUTHORS = authors_string
                book.TITLE_FULL = prod.name
                book.PRICE_PV = (
                    prod.list_price
                )  # precio con IVA. Depende de la config de Odoo!
                book.TAX_IVA = prod.taxes_id[0].amount  # IVA del libro (4 → 4.0%)
                book.PRICE_PVP = book.PRICE_PV / (
                    1 + book.TAX_IVA / 100
                )  # precio sin IVA
                book.PRICE_TYPE = c.PRICE_TYPE.FIXED[0]

                catalog.doc_lines.append(book)

            # Final details
            catalog.long_id_line.LEN = (
                len(catalog.doc_lines) + 2
            )  # implementation of this field varies

            # Build a SINLI email subject
            subject = Subject()
            subject.FROM = self.env.company.partner_id.sinli_id
            subject.TO = partner.sinli_id
            subject.DOCTYPE = (
                "LIBROS"  # TODO: can we get this string in a more generic way?
            )
            subject.VERSION = 9

            # Create attachment
            file_name = f"sinli_catalogo_{round(datetime.datetime.now().timestamp())}.txt"  # TODO: improve doc name
            file_data = base64.b64encode(str.encode(str(catalog), "windows-1252"))
            ir_values = {
                "name": file_name,
                "type": "binary",
                "datas": file_data,
                "store_fname": file_name,
                "mimetype": "text/plain; charset=windows-1252",
            }
            mail_attachment = self.env["ir.attachment"].create(ir_values)

            # Create email with attachment
            create_values = {
                "subject": str(subject),
                "email_from": self.env.company.partner_id.sinli_email,
                "email_to": partner.sinli_email,
                "recipient_ids": [partner.id],
                "reply_to": "",
                "attachment_ids": [mail_attachment.id]  # Incluir el ID del adjunto
            }
            mail = self.env["mail.mail"].create(create_values)
            # mail.attachment_ids = [(3, data_id.id)]
            mail.send()
            print(f"*****************{mail.state}")
            if mail.state == "sent":
                dialog_message += _("\nSinli email succesfully sent to %s") % partner.sinli_email
            else:
                dialog_message += _("\nSinli email could not be sent. Error %s.") % mail.state

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

    #         @api.multi
    # def enviar_correo(self):

    #     for registro in self:
    #         registro.message_post(
    #             body="Cuerpo del correo electrónico",
    #             subject="Asunto del correo electrónico",
    #             partner_ids=[1],  # Reemplaza con las IDs de los destinatarios
    #             subtype='mail.mt_comment',
    #             email_from="remitente@example.com",
    #             attachment_ids=[adjunto_id.id],
            # )

    @api.model
    def default_get(self, fields_list):
        rtn = super().default_get(fields_list)
        rtn["product_ids"] = [(6, 0, self.env.context.get("active_ids") or [])]
        return rtn
