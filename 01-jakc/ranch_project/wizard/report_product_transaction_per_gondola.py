import time
from openerp.osv import osv, fields

import logging

_logger = logging.getLogger(__name__)


class WizardReportProductTransactionPerGondola(osv.osv_memory):
    _name = 'wizard.report.product.transaction.per.gondola'

    _columns = {
        'stock_inventory_periode_id' : fields.many2one('stock.inventory.periode', 'Periode', required=True),
        'report_type': fields.selection([('01','Per Gondola'),('01','Per Product')], 'Type'),
        'iface_all_gondola' : fields.boolean('All Gondola', default=False),
        'gondola_ids' : fields.many2many('gondola', 'product_transaction_per_gondola_wizard', 'gondola_id',
                                         'wizard_id','Gondolas'),
        'iface_all_product' : fields.boolean('All Product', default=False),
        'product_ids' : fields.many2many('product.template','product_transaction_per_product_wizard', 'product_id',
                                          'wizard_id', 'Products')
    }

    def print_report(self, cr, uid, ids, context=None):
        _logger.info('Print Report')
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['stock_inventory_periode_id', 'iface_all_gondola', 'gondola_ids'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]

        return self.pool['report'].get_action(cr, uid, [], 'ranch_project.report_producttransactionpergondola', data=datas, context=context)

