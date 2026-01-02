from odoo import models, fields, api
import base64

import logging
_logger = logging.getLogger(__name__)

# as per https://odoo-development.readthedocs.io/en/latest/dev/py/external-imports.html
try:
    from stdnum import isbn
    from sinli import *
except ImportError as err:
    _logger.error(err)

class SinliProducts(models.Model):
    """ Extend product template for sinli management """

    _description = "Sinli Products"
    _inherit = 'product.template'


    def action_sinli_export_book(self):

        # Create a catalog document
        catalog = libros.v9.LibrosDoc()

        # TODO create a config to input sinli id and email
        catalog.long_id_line.FROM = "L1234567"
        catalog.short_id_line.FROM = "sinli@provider.example.org"

        # TODO show input files with autocomplete to load contact's sinli ids
        catalog.long_id_line.TO = "L9934567"
        catalog.short_id_line.TO = "sinli@library.example.org"

        # Create the header line of the doc
        header = libros.v9.LibrosDoc.Header()
        header.TYPE = "C"
        header.PROVIDER = self._context.get('default_company_id', self.env.company.display_name)
        header.CURRENCY = "E"

        catalog.doc_lines.append(header)

        # Create authors list
        author_names = [author.name for author in self.author_name]
        authors_string = ','.join(author_names) 

        # Create one book for the catalog document
        book = libros.v9.LibrosDoc.Book()
        book.EAN = self.barcode
        book.ISBN_INVOICE = isbn.format(self.isbn_number) if self.isbn_number else ""
        book.AUTHORS = authors_string
        book.TITLE_FULL = self.name
        book.PRICE_PV = self.list_price # precio con IVA. Depende de la config de Odoo!
        book.TAX_IVA = self.taxes_id[0].amount # IVA del libro (4 → 4.0%)
        book.PRICE_PVP = book.PRICE_PV / (1 + book.TAX_IVA / 100) # precio sin IVA
        book.PRICE_TYPE = "F"

        catalog.doc_lines.append(book)

        my_file = self.env['save.file.wizard'].create({
            'file_name': 'my-file.txt',
            'file_content': base64.b64encode(str.encode(str(catalog))),
        })

        _logger.error(f'*********** my_file: {my_file}')

        return {
            'name': ('Download File'),
            'res_id': my_file.id,
            'res_model': 'save.file.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('sinli.save_file_wizard_view_sinli').id,
            'view_mode': 'form',
            'view_type': 'form',
            }
