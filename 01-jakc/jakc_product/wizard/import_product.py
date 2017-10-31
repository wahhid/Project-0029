
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO


class ImportProduct(models.TransientModel):
    _name = 'import.product'
    _description = 'Import product'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=',', help='Default delimeter is ","')
    #location = fields.Many2one('stock.location', 'Default Location', required=True)

    @api.one
    def action_import(self):
        """Load Product data from the CSV file."""
        ctx = self._context
        product_obj = self.env['product.product']
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
            vals = {}
            vals.update({'name': str(row[3])})
            vals.update({'default_code': row[0]})
            vals.update({'type':'product'})
            vals.update({'categ_id':1})
            vals.update({'article_id': row[1]})
            vals.update({'uom_id':1})
            vals.update({'uom_po_id':1})
            res = self.env['product.template'].create(vals)


class StockInventoryImportLine(models.Model):
    _name = "stock.inventory.import.line"
    _description = "Stock Inventory Import Line"

    code = fields.Char('Product Code')
    product = fields.Many2one('product.product', 'Found Product')
    quantity = fields.Float('Quantity')
    inventory_id = fields.Many2one('stock.inventory', 'Inventory',
                                   readonly=True)
    location_id = fields.Many2one('stock.location', 'Location')
    lot = fields.Char('Product Lot')
    fail = fields.Boolean('Fail')
    fail_reason = fields.Char('Fail Reason')
