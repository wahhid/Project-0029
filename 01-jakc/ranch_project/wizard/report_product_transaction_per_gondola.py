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

AVAILABLE_GONDOLA_FILTER = [
    ('01','All Gondola'),
    ('02','Range Gondola'),
    ('03','Certain Gondola'),
]

AVAILABLE_PRODUCT_FILTER = [
    ('01','All Product'),
    ('03','Certain Product'),
]


class WizardReportProductTransactionPerGondola(models.TransientModel):
    _name = 'wizard.report.product.transaction.per.gondola'

    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode', 'Periode', required=True)
    report_type = fields.Selection([('01','Per Gondola'),('02','Per Product')], 'Type', required=True)
    report_category = fields.Selection([('01', 'Detail'), ('02', 'Summary')], 'Category', default='02', required=True)
    report_gondola_filter = fields.Selection(AVAILABLE_GONDOLA_FILTER, 'Gondola Filter', default='01', required=True)
    gondola_start_code = fields.Char('From', size=20)
    gondola_end_code = fields.Char('To', size=20)
    gondola_ids = fields.Many2many('gondola', 'product_transaction_per_gondola_wizard', 'gondola_id','wizard_id','Gondolas')
    report_product_filter = fields.Selection(AVAILABLE_PRODUCT_FILTER, "Product Filter", default='01', required=True)
    product_ids = fields.Many2many('product.template','product_transaction_per_product_wizard', 'product_id','wizard_id', 'Products')
    report_output = fields.Selection([('pdf','PDF'),('xls','XLSX')], 'Output', default='pdf', required=True)
    report_filename = fields.Char('Filename', size=100, readonly=True)
    report_file = fields.Binary('File', readonly=True)
    report_printed = fields.Boolean('Report Printed', default=False, readonly=True)
    state = fields.Selection([('before', 'Before'),('after', 'After'),],'Status', default='before')

    @api.multi
    def print_report(self):
        data = {}
        data['form'] = self.read(['stock_inventory_periode_id',
                                  'report_type',
                                  'report_category',
                                  'report_gondola_filter',
                                  'gondola_start_code',
                                  'gondola_end_code',
                                  'gondola_ids',
                                  'report_product_filter',
                                  'product_ids',
                                  'report_output',
                                  'state'])[0]

        if data['form']['report_output'] == 'pdf':
            #Print PDF Report
            if data['form']['report_type'] == '01':
                #Print Product Transcation Per Gondola (in PDF)
                return self.env['report'].get_action(self, 'ranch_project.report_producttransactionpergondola', data=data)
            else:
                #Print Gondola Transaction Per Product (in PDF)
                return self.env['report'].get_action(self, 'ranch_project.report_gondolatransactionperproduct', data=data)
        else:

            #Print Product Transaction Per Gondola (in Excel)
            fp = StringIO()
            workbook = xlsxwriter.Workbook(fp)
            column_heading_style = easyxf('font:height 200;font:bold True;')
            worksheet = workbook.add_worksheet('Source')
            worksheet.write(0, 0, _('Seq'))
            worksheet.write(0, 1, _('Diff'))
            worksheet.write(0, 2, _('Gondola'))
            worksheet.write(0, 3, _('Article #'))
            worksheet.write(0, 4, _('Product Name'))
            worksheet.write(0, 5, _('Quantity'))
            worksheet.write(0, 6, _('Exist'))
            worksheet.write(0, 7, _('Stock'))

            row = 1
            customer_row = 2

            for wizard in self:
                if wizard.report_type == '01':
                    #Report Per Gondola
                    if wizard.report_gondola_filter == '01':
                        #All Gondola
                        strSQL = """SELECT id FROM gondola ORDER BY code"""
                        self.env.cr.execute(strSQL)
                        ids = self.env.cr.fetchall()

                    if wizard.report_gondola_filter == '02':
                        #Range Gondola
                        strSQL = """SELECT id FROM gondola WHERE code BETWEEN '{}' AND '{}' ORDER BY code""".format(
                            wizard.gondola_start_code.upper(), wizard.gondola_end_code.upper())
                        _logger.info(strSQL)
                        self.cr.execute(strSQL)
                        ids = self.cr.fetchall()

                    if wizard.report_gondola_filter == '03':
                        #Certain Gongola
                        strSQL = """SELECT id FROM gondola WHERE id IN {}""".format(tuple(wizard.gondola_ids))
                        self.cr.execute(strSQL)
                        ids = self.cr.fetchall()

                    for id in ids:
                        if wizard.report_product_filter == '01':
                            args = [('stock_inventory_periode_id','=',wizard.stock_inventory_periode_id.id),
                                    ('gondola_id','=', id[0])]
                        if wizard.report_product_filter == '03':
                            product_ids = [x.id for x in wizard.product_ids]
                            args = [('stock_inventory_periode_id','=',wizard.stock_inventory_periode_id.id),
                                    ('gondola_id','=', id[0]),
                                    ('product_id', 'in', product_ids)]

                        stock_inventory_trans_line_obj = self.env['stock.inventory.trans.line']
                        stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.search(args)
                        for stock_inventory_trans_line_id in stock_inventory_trans_line_ids:
                            worksheet.write(row, 0, row)
                            if stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                _logger.info("Source ID Exist")
                                _logger.info(stock_inventory_trans_line_id.stock_inventory_trans_source_id)
                                _logger.info(stock_inventory_trans_line_id.stock_inventory_trans_source_id.iface_diff)
                                if stock_inventory_trans_line_id.stock_inventory_trans_source_id.iface_diff:
                                    _logger.info("Iface Diff")
                                    worksheet.write(row, 1, '*')
                            worksheet.write(row, 2, stock_inventory_trans_line_id.gondola_id.code)
                            worksheet.write(row, 3, stock_inventory_trans_line_id.article_id)
                            worksheet.write(row, 4, stock_inventory_trans_line_id.product_id.name)
                            qty = 0
                            if stock_inventory_trans_line_id.step == '1':
                                qty = stock_inventory_trans_line_id.qty1
                            if stock_inventory_trans_line_id.step == '2':
                                qty = stock_inventory_trans_line_id.qty2
                            if stock_inventory_trans_line_id.step == '3':
                                qty = stock_inventory_trans_line_id.qty3
                            worksheet.write(row, 5, qty)
                            if not stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                worksheet.write(row, 6, '*')
                            if stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                #worksheet.write(row, 7,stock_inventory_trans_line_id.stock_inventory_trans_source_id.product_theoretical_qty)
                                worksheet.write(row, 7, '')
                            row += 1
                    workbook.close()
                    excel_file = base64.encodestring(fp.getvalue())
                    wizard.report_file = excel_file
                    wizard.report_filename = 'product_transaction_per_gondola.xls'
                    wizard.report_printed = True
                    fp.close()

                if wizard.report_type == '02':
                    # Report Per Product
                    _logger.info('Report Per Product')
                    if wizard.report_product_filter == '01':
                        # All Gondola
                        strSQL = """SELECT distinct(product_id) as id FROM stock_inventory_trans_line WHERE stock_inventory_periode_id={}""".format(
                            wizard.stock_inventory_periode_id.id)
                        #strSQL = """SELECT id FROM product_template ORDER BY name"""
                        self.env.cr.execute(strSQL)
                        ids = self.env.cr.fetchall()
                    if wizard.report_product_filter == '03':
                        # Certain Gongola
                        if len(wizard.gondola_ids) > 1:
                            strSQL = """SELECT id FROM product_template WHERE id IN {} ORDER BY name""".format([wizard.gondola_ids[0]])
                        else:
                            strSQL = """SELECT id FROM product_template WHERE id IN {} ORDER BY name""".format(tuple(wizard.gondola_ids))

                        self.cr.execute(strSQL)
                        ids = self.cr.fetchall()

                    for id in ids:
                        if wizard.report_gondola_filter == '01':
                            args = [('stock_inventory_periode_id', '=', wizard.stock_inventory_periode_id.id),
                                    ('product_id', '=', id[0])]
                        if wizard.report_gondola_filter == '02':
                            args = [('stock_inventory_periode_id', '=', wizard.stock_inventory_periode_id.id),
                                    ('product_id', '=', id[0])]
                        if wizard.report_gondola_filter == '03':
                            args = [('stock_inventory_periode_id', '=', wizard.stock_inventory_periode_id.id),
                                    ('product_id', '=', id[0]),
                                    ('gondola_id', 'in', tuple(wizard.gondola_ids))]

                        stock_inventory_trans_line_obj = self.env['stock.inventory.trans.line']
                        stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.search(args)
                        for stock_inventory_trans_line_id in stock_inventory_trans_line_ids:
                            worksheet.write(row, 0, 0)
                            if stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                if stock_inventory_trans_line_id.stock_inventory_trans_source_id.iface_diff:
                                    worksheet.write(row, 1, '*')
                            worksheet.write(row, 2, stock_inventory_trans_line_id.gondola_id.code)
                            worksheet.write(row, 3, stock_inventory_trans_line_id.article_id)
                            worksheet.write(row, 4, stock_inventory_trans_line_id.product_id.name)
                            qty = 0
                            if stock_inventory_trans_line_id.step == '1':
                                qty = stock_inventory_trans_line_id.qty1
                            if stock_inventory_trans_line_id.step == '2':
                                qty = stock_inventory_trans_line_id.qty2
                            if stock_inventory_trans_line_id.step == '3':
                                qty = stock_inventory_trans_line_id.qty3
                            worksheet.write(row, 5, qty)
                            if not stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                worksheet.write(row, 6, '*')
                            if stock_inventory_trans_line_id.stock_inventory_trans_source_id:
                                worksheet.write(row, 7, '')
                            row += 1


                    workbook.close()
                    excel_file = base64.encodestring(fp.getvalue())
                    wizard.report_file = excel_file
                    wizard.report_filename = 'Gondola Transaction Per Produc.xls'
                    wizard.report_printed = True
                    fp.close()

            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'wizard.report.product.transaction.per.gondola',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }