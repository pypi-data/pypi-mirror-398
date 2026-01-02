from odoo import models, fields

class GetFile(models.TransientModel):

    _name = 'save.file.wizard'
    _description = 'Save File Wizard'

    file_name = fields.Char('File name', readonly=True)
    file_content = fields.Binary('File data', readonly=True,
        help='File(jpg, csv, xls, exe, any binary or text format)')
