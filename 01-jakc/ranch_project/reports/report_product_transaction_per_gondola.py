from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class product_transaction_per_gondola(report_sxw.rml_parse):

    def _get_stock_inventory_periode(self, id):
        stock_inventory_periode_obj = self.pool.get('stock.inventory.periode')
        return stock_inventory_periode_obj.browse(self.cr, self.uid, id)

    def _get_stock_inventory_trans(self, periode_id, gondola_id):
        trans_obj = self.pool.get('stock.inventory.trans')
        args = [('stock_inventory_periode_id','=', periode_id), ('gondola_id','=', gondola_id)]
        trans_ids = trans_obj.search(self.cr, self.uid, args)
        transs = trans_obj.browse(self.cr, self.uid, trans_ids)
        return transs

    def _get_trans_line(self, line_id):
        line_obj = self.pool.get('stock.inventory.trans.line')
        return line_obj.browse(self.cr, self.uid, line_id)

    def __init__(self, cr, uid, name, context):
        super(product_transaction_per_gondola, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_stock_inventory_periode': self._get_stock_inventory_periode,
            'get_stock_inventory_trans': self._get_stock_inventory_trans,
            'get_trans_line': self._get_trans_line,
        })


class report_product_transaction_per_gondola(osv.AbstractModel):
    _name = 'report.ranch_project.report_producttransactionpergondola'
    _inherit = 'report.abstract_report'
    _template = 'ranch_project.report_producttransactionpergondola'
    _wrapped_report_class = product_transaction_per_gondola
