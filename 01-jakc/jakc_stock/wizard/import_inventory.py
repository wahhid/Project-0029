
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO


class ImportInventory(models.TransientModel):
    _name = 'import.inventory'
    _description = 'Import inventory'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=';', help='Default delimeter is ","')
    location = fields.Many2one('stock.location', 'Default Location', required=True)

    @api.one
    def action_import(self):
        """Load Inventory data from the CSV file."""
        ctx = self._context
        stock_inventory_periode_obj = self.env['stock.inventory.periode']
        if 'active_id' in ctx:
            periode = stock_inventory_periode_obj.browse(ctx['active_id'])
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

        #Delete All Data
        strssql = """DELETE FROM stock_inventory_source WHERE stock_inventory_periode_id={}""".format(periode.id)
        self.env.cr.execute(strssql)

        #Import All Data
        for row in reader:
            print row
            strSQL = """INSERT INTO stock_inventory_source (
                        stock_inventory_periode_id, 
                        site, 
                        kode_pid, 
                        sequence, 
                        article_id, 
                        product_theoretical_qty, 
                        inventory_value) 
                        VALUES ({},'{}','{}',{},'{}',{},{})
                     """.format(periode.id , str(row[0]), str(row[1]), int(row[2]), str(row[3]), int(float(row[4])), int(float(row[5])))
            self.env.cr.execute(strSQL)
