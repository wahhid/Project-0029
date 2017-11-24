from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class article_transaction_per_gondola(report_sxw.rml_parse):

    def _get_stock_inventory_periode(self, id):
        stock_inventory_periode_obj = self.pool.get('stock.inventory.periode')
        return stock_inventory_periode_obj.browse(self.cr, self.uid, id)

    def _get_stock_inventory_trans_lines(self, trans_id, gondola_ids):
        line_obj = self.pool.get('stock.inventory.periode.line')
        args = [('stock_inventory_trans_id','=', trans_id), ('gondola_id','in', gondola_ids)]
        line_ids = line_obj.search(self.cr, self.uid, args)

    def _get_trans_line(self, line_id):
        line_obj = self.pool.get('stock.inventory.periode.line')
        return line_obj.browse(self.cr, self.uid, line_id)

    def __init__(self, cr, uid, name, context):
        super(article_transaction_per_gondola, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_stock_inventory_periode': self._get_stock_inventory_periode,
            'get_stock_inventory_trans_lines': self._get_stock_inventory_trans_lines,
            'get_trans_line': self._get_trans_line,
            'get_employee': self._get_employee,
        })


class report_article_transaction_per_gondola(osv.AbstractModel):
    _name = 'report.ranch_project.report_articletransactionpergondola'
    _inherit = 'report.abstract_report'
    _template = 'ranch_project.report_articletransactionpergondola'
    _wrapped_report_class = article_transaction_per_gondola

