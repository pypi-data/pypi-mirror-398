from odoo import fields, models
import random


class SinliResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sinli_email = fields.Char(string="SINLI Email", 
                              related='company_id.partner_id.sinli_email', 
                              readonly=False)
    
    sinli_id = fields.Char(string="SINLI ID",
                           related='company_id.partner_id.sinli_id',
                           readonly=False)
    
    sinli_default_pricelist_firm_sale = fields.Many2one(
            related='company_id.default_pricelist_firm_sale',
            string="Firm sales",
            readonly=False)
    
    sinli_default_pricelist_deposit_sale = fields.Many2one(
            related='company_id.default_pricelist_deposit_sale',
            string="Deposit sales",
            readonly=False)
    
    sinli_default_pricelist_fair_sale = fields.Many2one(
            related='company_id.default_pricelist_fair_sale',
            string="Book Fair / Sant Jordi sales",
            readonly=False)
    
    sinli_default_pricelist_other_sale = fields.Many2one(
            related='company_id.default_pricelist_other_sale',
            string="Other sales",
            readonly=False)
    

    def generate_random_sinli_test_id(self):
        random_num = random.choice(range(1,9999999))
        test_sinli_id = f"X{random_num:07}"
        self.sinli_id = test_sinli_id

