from odoo import fields, models

class SinliCompany(models.Model):
    """Extend res.company for SINLI management"""

    _inherit = "res.company"
    _check_company_auto = True

    default_pricelist_firm_sale = fields.Many2one(
        "product.pricelist",
        string="Default pricelist for firm sales imported from SINLI"
    )

    default_pricelist_deposit_sale = fields.Many2one(
        "product.pricelist",
        string="Default pricelist for deposit sales imported from SINLI"
    )

    default_pricelist_fair_sale = fields.Many2one(
        "product.pricelist",
        string="Default pricelist for fair sales imported from SINLI"
    )

    default_pricelist_other_sale = fields.Many2one(
        "product.pricelist",
        string="Default pricelist for other sales imported from SINLI"
    )