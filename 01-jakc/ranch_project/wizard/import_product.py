
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO


class ImportProduct(models.TransientModel):
    _name = 'import.product'
    _description = 'Import product'

    @api.multi
    def _get_product_by_ean(self, ean):
        product_template_obj = self.env['product.template']
        args = [('ean', '=', ean)]
        product_template_ids = product_template_obj.search(args)
        if len(product_template_ids) > 0:
            return product_template_ids
        else:
            return False

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

        reader = csv.reader(file_input, delimiter=delimeter, lineterminator='\r\n')

        i = 0
        for row in reader:
            i += 1

            # print i
            # vals = {}
            # vals.update({'name': str(row[3])})
            # vals.update({'default_code': row[0]})
            # vals.update({'type': 'product'})
            # vals.update({'categ_id': 1})
            # vals.update({'article_id': row[1]})
            # vals.update({'uom_id': 1})
            # vals.update({'uom_po_id': 1})
            # res = self.env['product.template'].create(vals)
            product_template = self._get_product_by_ean(str(row[0]))
            if not product_template:
                strsql = """INSERT INTO product_template (
                             name,
                             ean,
                             type,
                             categ_id,
                             marchandise_id,
                             article_id,
                             uom_id,
                             sap_uom_id,
                             uom_po_id, 
                             tracking, 
                             active) 
                             VALUES ('{}', '{}', '{}', {}, '{}', {} , {}, '{}' , '{}', '{}', {}) RETURNING id
                         """ \
                    .format(str(row[3].replace("'", " ")).decode('unicode_escape').encode('ascii', 'ignore'),
                            str(row[0]),
                            'product',
                            str(1),
                            str(row[2]),
                            str(row[1]),
                            str(1),
                            str(row[4]),
                            str(1),
                            'none',
                            'true')
                self.env.cr.execute(strsql)

                id = self.env.cr.fetchone()[0]
                strsql = """INSERT INTO product_product(
                             product_tmpl_id, 
                             default_code,
                             active) 
                             VALUES ({},'{}',{})
                          """ \
                    .format(id,
                            str(row[0]),
                            'true')
                self.env.cr.execute(strsql)
            else:
                strsql = """UPDATE product_template SET
                             name='{}',
                             ean='{}',
                             type='{}',
                             categ_id={},
                             marchandise_id='{}',
                             article_id='{}',
                             sap_uom_id='{}',
                             uom_po_id={},
                             tracking='{}',
                             active={}
                             WHERE id={}
                         """ \
                    .format(str(row[3].replace("'", " ").decode('unicode_escape').encode('ascii', 'ignore')),
                            str(row[0]),
                            'product',
                            str(1),
                            str(row[2]),
                            str(row[1]),
                            str(row[4]),
                            str(1),
                            'none',
                            'true',
                            product_template[0].id)
                self.env.cr.execute(strsql)

                strsql = """UPDATE product_product SET
                             default_code='{}',
                             active={}
                             WHERE product_tmpl_id={}
                         """.format(str(row[0]),
                                    'true',
                                    product_template[0].id)
                self.env.cr.execute(strsql)

        for row in reader:
            product_ids = product_obj.search([('default_code','=', row[0])])
            if not product_ids:
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
