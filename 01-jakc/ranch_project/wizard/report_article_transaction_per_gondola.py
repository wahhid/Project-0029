from openerp import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class WizardReportArticleTransactionPerGondola(models.TransientModel):
    _name = 'wizard.report.article.transaction.per.gondola'

    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode','Periode', required=True)
    iface_all_gondola = fields.Boolean('All Gondola', default=False)
    gondola_ids = fields.Many2many('gondola', 'article_transaction_per_gondola_wizard','wizard_id', 'gondola_id', 'Gondola')

    @api.one
    def print_report(self):
        _logger.info('Print Report')


