from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
from sinli.subject import Subject
from sinli.doctype import DocumentType
import re, base64
import logging
from .sinli_mixin import SinliImportMixin

_logger = logging.getLogger(__name__)


class SinliDialog(models.TransientModel):
    _name = 'sinli.dialog'
    _description = 'SINLI Dialog'

    message = fields.Text(string='Message', readonly=True, required=True)


class SinliMessage(models.Model):
    _name = 'sinli.message'
    _description = 'SINLI message'
    _rec_name = 'type'
    _inherit = ['mail.thread', 'sinli.import.mixin']

    sender_email = fields.Char('Sender email')
    sender = fields.Many2one(
        'res.partner', 'Sender', ondelete='set null',
        domain=[('speak_sinli', '=', True)],
        help="Sender contact, if not exists it's empty")
    date = fields.Datetime(
        'Date', default=fields.Datetime.now(),
        help="Date of the message.")
    import_date = fields.Datetime('Import date', required=False)
    import_user = fields.Many2one(
        'res.partner', 'Import user', ondelete='set null',
        help="User that imported the message.")
    type = fields.Char('Type of message', required=True)
    imported = fields.Boolean('Imported', default=False,
                              help='True if the message was imported')
    valid_format = fields.Boolean('Valid format', default=False,
                                  help='True if the message has a valid format')
    sinli_attachment = fields.Many2one('ir.attachment', 'Sinli Attachment', copy=False)
    generated_document = fields.Reference(string="Generated Document",
        selection=[
            ('sale.order', 'Orden de Venta'),
            ('purchase.order', 'Orden de Compra'),
            ('stock.return.picking', 'Devolución')
        ],
        help="References to the document generated after import.")

    # Overrides mail_thread message_new that is called by the mailgateway
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        _logger.info("######## New SINLI message received #########")
        if custom_values is None:
            custom_values = {}

        email_from = msg_dict.get('from')
        mail_subject = msg_dict.get('subject')
        valid_format = False

        readable_subject = Subject.from_str(mail_subject)
        if readable_subject.is_valid():
            msg_dict["subject"] = mail_subject
            valid_format = True

        # Get the email from address    
        email_pattern = r'[\w.+-]+@[\w.-]+'
        email_from = re.search(email_pattern, email_from).group(0)

        values = {
            'type': mail_subject,
            'sender_email': email_from,
            'valid_format': valid_format,
            'date': fields.Datetime.now(),
        }

        # Get the partner from the mail if any, else partner will be empty
        partner = self.env['res.partner'].search([('sinli_email', 'ilike', email_from)], limit=1)
        if partner:
            values['sender'] = partner.id

        custom_values.update(values)
        sinli_message = super().message_new(msg_dict, custom_values=custom_values)

        if msg_dict.get('attachments'):
            first_attachment = msg_dict['attachments'][0]
            attachment_content = first_attachment[1]
            content_bytes = attachment_content.encode('windows-1252', errors='ignore')
            datas_bytes = base64.b64encode(content_bytes)
            datas_str = datas_bytes.decode('ascii')

            attachment = self.env['ir.attachment'].create({
                'name': first_attachment[0],
                'datas': datas_str,
                'res_model': self._name,
                'res_id': sinli_message.id,
            })
            sinli_message.sinli_attachment = attachment.id

        _logger.info("###### New SINLI message successfully processed #######")
        return sinli_message

    def import_sinli_message(self):
        if not self.sender:
            raise ValidationError("It is not possible to import an order without a contact.")

        if not self.sinli_attachment:
            self._generate_sinli_attachment()

        sinli_message = self._get_sinli_message(self.sinli_attachment.datas)
        _logger.info("Importing SINLI message: %s", sinli_message)

        if not sinli_message:
            raise ValidationError("There was an error processing the SINLI message.")
        
        contacts_validation_error = self._validate_sinli_ids(sinli_message, self.sender)
        if contacts_validation_error:
            dialog_message = contacts_validation_error
        else:
            # Process catalog messages
            if sinli_message.doctype_code == DocumentType.LIBROS.name:
                dialog_message = self._import_products(sinli_message, self.sender)
                self.imported = True
            # Process sale/purchase orders messages
            if sinli_message.doctype_code in (DocumentType.PEDIDO.name, DocumentType.ENVIO.name):
                import_method = {
                    DocumentType.PEDIDO.name: self._import_sale_order,
                    DocumentType.ENVIO.name: self._import_purchase_order
                }[sinli_message.doctype_code]
                
                result_message = import_method(sinli_message, self.sender)
                if isinstance(result_message, tuple):
                    dialog_message, order = result_message
                    self._mark_message_as_imported(order)
                else:
                    dialog_message = result_message
            else:
                dialog_message = _("No valid message type detected for import.")

        sinli_dialog = self.env['sinli.dialog'].create({'message': dialog_message})
        return {
            'name': 'SINLI Import',
            'type': 'ir.actions.act_window',
            'res_model': 'sinli.dialog',
            'view_id': self.env.ref('sinli.sinli_dialog_view_form').id,
            'view_mode': 'form',
            'target': 'new',
            'res_id': sinli_dialog.id,
        }
    
