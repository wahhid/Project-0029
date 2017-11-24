from openerp import models, fields, api, exceptions, _
from datetime import datetime
import base64
import StringIO
import logging

_logger = logging.getLogger(__name__)


class Gondola(models.Model):
    _name = 'gondola'

    stock_warehouse_id = fields.Many2one('stock.warehouse','warehouse #')
    code = fields.Char('Code', size=20, required=True)
    name = fields.Char('Name', size=100, required=True)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    gondola_ids = fields.One2many('gondola','stock_warehouse_id','Gondolas')


class StockInventoryPeriode(models.Model):
    _name = 'stock.inventory.periode'

    @api.one
    def trans_open(self):
        self.write({'state':'open'})

    @api.one
    def trans_close(self):
        self.write({'state': 'done'})

    @api.one
    def trans_re_open(self):
        self.write({'state': 'open'})

    @api.one
    def trans_calculate(self):
        print "Trans Calculate"
        for trans in self.stock_inventory_trans_ids:
            _logger.info('Process : ' + str(trans.id))
            trans.trans_calculate()
        self.iface_calculate = True
        self.datetime_calculate = datetime.now()

    @api.one
    def trans_generate_file(self):
        output = StringIO.StringIO()
        for source in self.stock_inventory_source_ids:
            content = "{};{};{};{};{};{};{}\n".format(source.site, source.kode_pid, str(source.sequence), source.article_id, str(source.product_theoretical_qty), str(source.product_real_qty), str(source.inventory_value))
            output.write(content)
        self.sap_csv_file = base64.encodestring(output.getvalue())

    def _get_sap_csv_url(self):
        self.sap_csv_url = "/csv/download/sap/{}/".format(self.id)

    @api.model
    def _sap_csv_download(self, vals):
        sql = """SELECT 
                     quote_nullable(site),
                     quote_nullable(kode_pid),
                     quote_nullable(sequence),
                     quote_nullable(article_id),
                     quote_nullable(product_thoeretical_qyt),
                     quote_nullable(product_real_qty),
                     quote_nullable(inventory_value),
                 FROM
                     stock_inventory_source
                 WHERE stock_inventory_periode_id={}""".format(vals.get('periode_id'))
        self.env.cr.execute(sql)
        rows = self.env.cr.fetchall()
        csv = ''
        if rows:
            for row in rows:
                csv_row = ""
                for item in row:
                    csv_row += "{};".format(item)
                csv += "{}\n".format(csv_row[:-1])
        return csv

    @api.multi
    def action_stock_inventory_source_tree(self):
        periode = self
        action = self.env['ir.model.data'].xmlid_to_object('ranch_project.action_stock_inventory_source_tree2').read()[0]
        action['context'] = {
            'default_stock_inventory_periode_id': periode.id,
        }
        return action

    @api.multi
    def action_stock_inventory_trans_tree(self):
        periode = self
        action = self.env['ir.model.data'].xmlid_to_object('ranch_project.action_stock_inventory_trans_tree2').read()[0]
        action['context'] = {
            'default_stock_inventory_periode_id': periode.id,
        }
        return action

    @api.multi
    def action_stock_inventory_trans_line_tree(self):
        periode = self
        action = self.env['ir.model.data'].xmlid_to_object('ranch_project.action_stock_inventory_trans_line_tree2').read()[0]
        action['context'] = {
            'default_stock_inventory_periode_id': periode.id,
        }
        return action

    name = fields.Char('Name', size=50, required=True)
    trans_date = fields.Date('Date', index=True)
    location_id = fields.Many2one('stock.location','Location', index=True)
    sap_csv_url = fields.Char(compute='_get_csv_url')
    iface_calculate = fields.Boolean('Calculated', default=False)
    datetime_calculate = fields.Datetime('Calculate Time')
    sap_csv_file = fields.Binary('SAP File', readonly=True)
    stock_inventory_source_ids = fields.One2many('stock.inventory.source','stock_inventory_periode_id', 'Sources')
    stock_inventory_trans_ids = fields.One2many('stock.inventory.trans','stock_inventory_periode_id', 'Transactions')
    state = fields.Selection([('draft','New'),('open','Open'),('done','Close')], 'Status', default='draft')


class StockInventorySource(models.Model):
    _name = 'stock.inventory.source'

    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode','Periode #', index=True)
    site = fields.Char('Site', size=20, index=True)
    kode_pid = fields.Char('Kode PID', size=20, index=True)
    sequence = fields.Integer('Sequence')
    article_id = fields.Char('Article #', size=50, index=True)
    product_theoretical_qty = fields.Float('Theoretical Qty', default=0.0)
    product_real_qty = fields.Float('Real Qty', default=0.0)
    inventory_value = fields.Float('Inventory Value', default=0.0)


class StockInventoryTrans(models.Model):
    _name = 'stock.inventory.trans'

    @api.multi
    def name_get(self):
        res = super(StockInventoryTrans, self).name_get()
        data = []
        for trans in self:
            display_value = trans.stock_inventory_periode_id.name
            display_value += " - "
            display_value += trans.gondola_id.name
            data.append((trans.id, display_value))
        return data

    @api.one
    def trans_next_step(self):
        trans = self
        if trans.step == '1':
            self.write({'step':'2'})
        if trans.step == '2':
            self.write({'step': '3'})

    @api.one
    def trans_calculate(self):
        stock_inventory_source_obj = self.env['stock.inventory.source']
        strsql = """SELECT distinct(article_id) FROM stock_inventory_trans_line WHERE stock_inventory_trans_id={}""".format(self.id)
        self.env.cr.execute(strsql)
        articles = self.env.cr.fetchall()
        for article in articles:
            if self.step == '1':
                strsql = """SELECT sum(qty1) FROM stock_inventory_trans_line WHERE stock_inventory_trans_id={} AND article_id='{}'""".format(self.id, article[0])
            if self.step == '2':
                strsql = """SELECT sum(qty2) FROM stock_inventory_trans_line WHERE stock_inventory_trans_id={} AND article_id='{}'""".format(self.id, article[0])
            if self.step == '3':
                strsql = """SELECT sum(qty3) FROM stock_inventory_trans_line WHERE stock_inventory_trans_id={} AND article_id='{}'""".format(self.id, article[0])

            self.env.cr.execute(strsql)
            quantity =  self.env.cr.fetchone()[0]
            args = [('stock_inventory_periode_id','=', self.stock_inventory_periode_id.id),('article_id','=',article[0])]
            stock_inventory_source_ids = stock_inventory_source_obj.search(args)
            for stock_inventory_source in stock_inventory_source_ids:
                stock_inventory_source.product_real_qty = quantity
        self.iface_calculate = True
        self.datetime_calculate = datetime.now()

    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode','Periode #')
    gondola_id = fields.Many2one('gondola','Gondola', index=True)
    user_id = fields.Many2one('res.users', 'User', index=True)
    step = fields.Selection([('1','First Collection'),('2','Second Collection'),('3','Third Collection')], 'Step', default='1')
    iface_calculate = fields.Boolean('Calculated', default=False)
    datetime_calculate = fields.Datetime('Calculate Time')
    state = fields.Selection([('open','Open'),('done','Close')], 'Status')
    line_ids = fields.One2many('stock.inventory.trans.line', 'stock_inventory_trans_id', 'Lines')

class StockInventoryTransLine(models.Model):
    _name = 'stock.inventory.trans.line'

    stock_inventory_trans_id = fields.Many2one('stock.inventory.trans','Transaction #', index=True)
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    gondola_id = fields.Many2one(comodel_name='gondola', string='Gondola', related='stock_inventory_trans_id.gondola_id')
    product_id = fields.Many2one('product.template','Product')
    article_id = fields.Char('Article #', size=20)
    user_id = fields.Many2one(comodel_name='res.users', string='User', related='stock_inventory_trans_id.user_id')
    qty1 = fields.Float('Qty 1')
    qty2 = fields.Float('Qty 2')
    qty3 = fields.Float('Qty 3')



