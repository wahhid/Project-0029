import time
from openerp.osv import osv, fields

import logging

_logger = logging.getLogger(__name__)


class WizardReportArticleTransaction(osv.osv_memory):
    _name = 'wizard.report.article.transaction'

    _columns = {
        'stock_inventory_periode_id' : fields.many2one('stock.inventory.periode', 'Periode', required=True),
        'report_type': fields.selection([('01','All'),('02','Diffrent Only'),('03','Match Only')],'Type', required=True),
    }

    _defaults = {
        'report_type': lambda *a: '01',
    }

    def print_report(self, cr, uid, ids, context=None):
        _logger.info('Print Report')
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['stock_inventory_periode_id', 'report_type'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]

        return self.pool['report'].get_action(cr, uid, [], 'ranch_project.report_articletransaction', data=datas, context=context)

