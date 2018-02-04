import time
from openerp.osv import osv, fields

import logging

_logger = logging.getLogger(__name__)

AVAILABLE_GONDOLA_FILTER = [
    ('01','All Gondola'),
    ('02','Range Gondola'),
    ('03','Certain Gondola'),
]

AVAILABLE_PRODUCT_FILTER = [
    ('01','All Product'),
    ('03','Certain Product'),
]


class WizardReportProductTransactionPerGondola(osv.osv_memory):
    _name = 'wizard.report.product.transaction.per.gondola'

    _columns = {
        'stock_inventory_periode_id' : fields.many2one('stock.inventory.periode', 'Periode', required=True),
        'report_type': fields.selection([('01','Per Gondola'),('02','Per Product')], 'Type', required=True),
        'report_category': fields.selection([('01', 'Detail'), ('02', 'Summary')], 'Category', required=True),
        'report_gondola_filter': fields.selection(AVAILABLE_GONDOLA_FILTER, 'Gondola Filter', required=True),
        'gondola_start_code': fields.char('From', size=20),
        'gondola_end_code': fields.char('To', size=20),
        'gondola_ids' : fields.many2many('gondola', 'product_transaction_per_gondola_wizard', 'gondola_id',
                                         'wizard_id','Gondolas'),
        'report_product_filter': fields.selection(AVAILABLE_PRODUCT_FILTER, "Product Filter", required=True),
        'product_ids' : fields.many2many('product.template','product_transaction_per_product_wizard', 'product_id',
                                          'wizard_id', 'Products')
    }

    _defaults = {
        'report_category': lambda *a: '02',
        'report_gondola_filter': lambda *a: '01',
        'report_product_filter': lambda *a: '01',
    }

    def print_report(self, cr, uid, ids, context=None):
        _logger.info('Print Report')
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['stock_inventory_periode_id',
                                       'report_type',
                                       'report_category',
                                       'report_gondola_filter',
                                       'gondola_start_code',
                                       'gondola_end_code',
                                       'gondola_ids',
                                       'report_product_filter',
                                       'product_ids',], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id', False):
            datas['ids'] = [res['id']]

        if res['report_type'] == '01':
            return self.pool['report'].get_action(cr, uid, [], 'ranch_project.report_producttransactionpergondola', data=datas, context=context)
        else:
            return self.pool['report'].get_action(cr, uid, [], 'ranch_project.report_gondolatransactionperproduct', data=datas, context=context)

