from odoo import _, fields, models

import logging
_logger = logging.getLogger(__name__)


class ImportSinliFile(models.TransientModel):
    _name = "import.sinli.file"
    _description = "Import Sinli File"
    _inherit = ['sinli.import.mixin']

    sinli_file = fields.Binary(string="Sinli order file", required=True)

    def import_sale_orders(self):
        sinli_message = self._get_sinli_message(self.sinli_file)
        _logger.info("## Importing sale order from SINLI file")

        # Search for the sender partner using the SINLI ID
        sender = self._find_partner_by_sinli_id(sinli_message.long_id_line.FROM)
        
        contacts_validation_error = self._validate_sinli_ids(sinli_message, sender)
        if contacts_validation_error:
            dialog_message = contacts_validation_error

        result_message = self._import_sale_order(sinli_message, sender)
        dialog_message = result_message[0] if isinstance(result_message, tuple) else result_message

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
    
    def import_purchase_orders(self):
        sinli_message = self._get_sinli_message(self.sinli_file)
        _logger.info("## Importing purchase order from SINLI file")
        
        # Search for the sender partner using the SINLI ID
        sender = self._find_partner_by_sinli_id(sinli_message.long_id_line.FROM)
        
        contacts_validation_error = self._validate_sinli_ids(sinli_message, sender)
        if contacts_validation_error:
            dialog_message = contacts_validation_error

        result_message = self._import_purchase_order(sinli_message, sender)
        dialog_message = result_message[0] if isinstance(result_message, tuple) else result_message

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