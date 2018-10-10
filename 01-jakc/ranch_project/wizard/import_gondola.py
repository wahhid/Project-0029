
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO


class ImportGondola(models.TransientModel):
    _name = 'import.gondola'
    _description = 'Import Gondola'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=',', help='Default delimeter is ","')
    #location = fields.Many2one('stock.location', 'Default Location', required=True)

    @api.one
    def action_import(self):
        """Load Product data from the CSV file."""
        ctx = self._context
        product_obj = self.env['gondola']
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)

        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','

        reader = csv.reader(file_input, delimiter=delimeter,lineterminator='\r\n')

        for row in reader:
            product_ids = product_obj.search([('code','=', row[0])])
            if not product_ids:
                vals = {}
                vals.update({'code': row[0]})
                vals.update({'name': str(row[1])})
                res = self.env['gondola'].create(vals)


