from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
import re

class SinliPartners(models.Model):
    """ Extend res.partner template for SINLI management """

    _description = "Sinli Partners"
    _inherit = 'res.partner'

    sinli_email = fields.Char(string="SINLI Email")
    sinli_id = fields.Char(string="SINLI ID")
    speak_sinli = fields.Boolean(compute='_speak_sinli', string="Speak SINLI", help="True if the contact has valid SINLI ID and SINLI email.")

    @api.constrains('sinli_email')
    def _check_email_format(self):
        for record in self:
            if record.sinli_email:
                duplicates = self.env['res.partner'].search([('sinli_email', '=', record.sinli_email)])
                if len(duplicates) > 1:
                    raise ValidationError(_("This SINLI email is already in use."))
                if not re.match(r"[^@]+@[^@]+\.[^@]+", record.sinli_email):
                    raise ValidationError(_("The email has an invalid format."))
                
    @api.constrains('sinli_id')
    def _check_sinli_id_format(self):
        for record in self:
            if record.sinli_id:
                duplicates = self.env['res.partner'].search([('sinli_id', '=', record.sinli_id)])
                if len(duplicates) > 1:
                    raise ValidationError(_("This SINLI ID is already in use."))
                if not re.match(r'^[A-Za-z0-9]{8}$', record.sinli_id):
                    raise ValidationError(_("The ID for SINLI does not satisfy any of the supported formats, where 'n' is a number: \nLIBnnnnn \nLnnnnnnn \nXnnnnnnn"))
                
    def _speak_sinli(self):
        self.speak_sinli = self.sinli_email and self.sinli_id