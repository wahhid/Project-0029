
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO


class ImportInventory(models.TransientModel):
    _name = 'import.inventory'
    _description = 'Import inventory'

    def _get_default_location(self):
        ctx = self._context
        if 'active_id' in ctx:
            inventory_obj = self.env['stock.inventory']
            inventory = inventory_obj.browse(ctx['active_id'])
        return inventory.location_id

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    iface_product_name = fields.Boolean('Using Product Name', default=False)
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')
    location = fields.Many2one('stock.location', 'Default Location',
                               default=_get_default_location, required=True)

    @api.one
    def action_import(self):
        """Load Inventory data from the CSV file."""
        ctx = self._context
        stloc_obj = self.env['stock.location']
        inventory_obj = self.env['stock.inventory']
        inv_imporline_obj = self.env['stock.inventory.import.line']
        product_obj = self.env['product.product']
        if 'active_id' in ctx:
            inventory = inventory_obj.browse(ctx['active_id'])
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        location = self.location
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,lineterminator='\r\n')

        values = {}
        actual_date = fields.Date.today()
        inv_name = self.name + ' - ' + actual_date
        inventory.write({'name': inv_name,
                         'date': fields.Datetime.now(),
                         'imported': True, 'state': 'confirm'})
        for row in reader:
            print row
            val = {}
            prod_location = location.id
            prod_lst = product_obj.search([('default_code', '=', row[3])])
            if prod_lst:
                #val['product'] = prod_lst[0].id
                product_id = prod_lst[0].id
            else:
                product_id = 'null'

            #val['code'] = row[3]
            #val['quantity'] = row[4]
            #val['location_id'] = prod_location
            #val['inventory_id'] = inventory.id
            #val['fail'] = True
            #val['fail_reason'] = _('No processed')
            #inv_imporline_obj.create(val)

            strSQL = """INSERT INTO stock_inventory_import_line (product,code,quantity,location_id,inventory_id,fail,fail_reason) 
                        VALUES ({},'{}',{},{},{},{},'{}')
                     """.format(product_id, str(row[3]), int(float(row[4])), prod_location, inventory.id, 'true', 'No processed')
            self.env.cr.execute(strSQL)

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
