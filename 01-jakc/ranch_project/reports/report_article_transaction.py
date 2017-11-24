from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw

class article_transaction(report_sxw.rml_parse):

    def _get_stock_inventory_periode(self, id):
        stock_inventory_periode_obj = self.pool.get('stock.inventory.periode')
        return stock_inventory_periode_obj.browse(self.cr, self.uid, id)

    def _get_source_line(self, line_id):
        source_obj = self.pool.get('stock.inventory.source')
        return source_obj.browse(self.cr, self.uid, line_id)

    def __init__(self, cr, uid, name, context):
        super(article_transaction, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_stock_inventory_periode': self._get_stock_inventory_periode,
            'get_source_line': self._get_source_line,
        })


class report_article_transaction(osv.AbstractModel):
    _name = 'report.ranch_project.report_articletransaction'
    _inherit = 'report.abstract_report'
    _template = 'ranch_project.report_articletransaction'
    _wrapped_report_class = article_transaction
