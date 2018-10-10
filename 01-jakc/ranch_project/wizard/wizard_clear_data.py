from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, UserError, Warning


class ImportProduct(models.TransientModel):
    _name = 'wizard.clear.data'
    _description = 'Clear Data'

    iface_clear_data = fields.Boolean('Clear Data', default=False)


    @api.multi
    def delete_gondolas(self):
        strSQL = 'DELETE FROM gondola'
        self.env.cr.execute(strSQL)

    @api.multi
    def delete_products(self):
        strSQL = 'DELETE FROM product_template'
        self.env.cr.execute(strSQL)

    @api.multi
    def delete_periodes(self):
        stock_inventory_periode_obj = self.env['stock.inventory.periode']
        stock_inventory_periode_ids = stock_inventory_periode_obj.search([])
        for periode in stock_inventory_periode_ids:
            periode.unlink()

    @api.one
    def process_clear_data(self):
        if self.iface_clear_data:
            #Clear All Periode
            self.delete_periodes()
            #Clear All Gondola
            self.delete_gondolas()
            #Clear All Product
            self.delete_products()


