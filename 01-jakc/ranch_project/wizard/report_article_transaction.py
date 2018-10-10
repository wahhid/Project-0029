
from openerp import models, fields, api, _
import xlwt
import xlsxwriter
from cStringIO import StringIO
import base64
from xlwt import easyxf
import datetime
import time
import logging

_logger = logging.getLogger(__name__)


class WizardReportArticleTransaction(models.TransientModel):
    _name = 'wizard.report.article.transaction'

    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode', 'Periode', required=True)
    report_type = fields.Selection([('01', 'All'), ('02', 'Diffrent Only'), ('03', 'Match Only')], 'Type', default='01', required=True)
    report_file = fields.Binary('File', readonly=True)
    report_filename = fields.Char('Filename', size=100, readonly=True, default='Article Transaction Report.xlsx')
    report_printed = fields.Boolean('Payment Report Printed', default=False, readonly=True)


    @api.multi
    def action_print_report(self):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_worksheet('Source')
        worksheet.write(0, 0, _('Site ID'))
        worksheet.write(0, 1, _('Kode PID'))
        worksheet.write(0, 2, _('Sequence'))
        worksheet.write(0, 3, _('Article #'))
        worksheet.write(0, 4, _('Theoritical QTY'))
        worksheet.write(0, 5, _('Real QTY'))
        worksheet.write(0, 6, _('Diff QTY'))
        worksheet.write(0, 7, _('Inventory Value'))
        worksheet.write(0, 8, _('Value Diff'))
        worksheet.write(0, 9, _('Diff'))

        row = 1
        customer_row = 2

        for wizard in self:
            stock_inventory_source_ids = []
            if wizard.report_type == '01':
                stock_inventory_source_ids = wizard.stock_inventory_periode_id.stock_inventory_source_ids
            if wizard.report_type == '02':
                args = [('stock_inventory_periode_id', '=', wizard.stock_inventory_periode_id.id),
                        ('iface_diff', '=', True)]
                stock_inventory_source_ids = self.env['stock.inventory.source'].search(args)

            if wizard.report_type == '02':
                args = [('stock_inventory_periode_id', '=', wizard.stock_inventory_periode_id.id),
                        ('iface_diff', '=', False)]
                stock_inventory_source_ids = self.env['stock.inventory.source'].search(args)

            for source in stock_inventory_source_ids:
                _logger.info("Row : " + str(row))
                worksheet.write(row, 0, source.site)
                worksheet.write(row, 1, source.kode_pid)
                worksheet.write(row, 2, source.sequence)
                worksheet.write(row, 3, source.article_id)
                worksheet.write(row, 4, source.product_theoretical_qty)
                worksheet.write(row, 5, source.product_real_qty)
                worksheet.write(row, 6, source.product_diff_qty)
                worksheet.write(row, 7, source.inventory_value)
                worksheet.write(row, 8, source.inventory_value_diff)
                worksheet.write(row, 9, source.iface_diff)
                row += 1

            workbook.close()

            excel_file = base64.encodestring(fp.getvalue())
            wizard.report_file = excel_file
            wizard.report_printed = True
            fp.close()

            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'wizard.report.article.transaction',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }


    @api.multi
    def action_print_report_01(self,):
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Source')

        worksheet.write(1, 0, _('Site ID') )
        worksheet.write(1, 1, _('Kode PID'))
        worksheet.write(1, 2, _('Sequence'))
        worksheet.write(1, 3, _('Article #'))
        worksheet.write(1, 4, _('Theoritical QTY'))
        worksheet.write(1, 5, _('Real QTY'), column_heading_style)
        worksheet.write(1, 6, _('Diff QTY'), column_heading_style)
        worksheet.write(1, 7, _('Inventory Value'), column_heading_style)
        worksheet.write(1, 8, _('Value Diff'), column_heading_style)
        worksheet.write(1, 9, _('Diff'), column_heading_style)

        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).height = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).height = 5000

        row = 2
        customer_row = 2

        for wizard in self:
            heading = 'Source Report'
            worksheet.write_merge(0, 0, 0, 9, heading, easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))

            for source in wizard.stock_inventory_periode_id.stock_inventory_source_ids:
                _logger.info("Row : " + str(row))
                worksheet.write(row, 0, source.site)
                worksheet.write(row, 1, source.kode_pid)
                worksheet.write(row, 2, source.sequence)
                worksheet.write(row, 3, source.article_id)
                worksheet.write(row, 4, source.product_theoretical_qty)
                worksheet.write(row, 5, source.product_real_qty)
                worksheet.write(row, 6, source.product_diff_qty)
                worksheet.write(row, 7, source.inventory_value)
                worksheet.write(row, 8, source.inventory_value_diff)
                worksheet.write(row, 9, source.iface_diff)
                row += 1

            fp = StringIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.report_file = excel_file
            wizard.report_filename = 'Payment Summary Report.xls'
            wizard.report_printed = True
            fp.close()
            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'wizard.report.article.transaction',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }