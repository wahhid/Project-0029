from openerp import fields, models, exceptions, api, _
import base64
import csv
import StringIO


class ExportAllData(models.TransientModel):
    _name = 'export.all.data'
    _description = 'Export All Data'


    stock_inventory_periode_id = fields.Many2one('stock.inventory.periode','Periode', required=True)
    product_attachment = fields.Binary('Product', readonly=True)
    product_attachment_filename = fields.Char('Product Filename', size=100, readonly=True)
    gondola_attachment = fields.Binary('Gondola', readonly=True)
    gondola_attachment_filename = fields.Char('Gondola Filename', size=100, readonly=True)
    source_attachment = fields.Binary('Source', readonly=True)
    source_attachment_filename = fields.Char('Source Filename', size=100, readonly=True)
    periode_trans_attachment = fields.Binary('Periode Transaction', readonly=True)
    periode_trans_attachment_filename = fields.Char('Periode Transaction Filename', size=100, readonly=True)
    iface_generated = fields.Boolean('Generated', default=False)

    @api.multi
    def action_export(self):
        for wizard in self:
            output = StringIO.StringIO()
            output.write("articleid;ean;marchandisid;product_name;uom;\r\n")
            sql = """SELECT 
                        article_id, ean, marchandise_id, name, sap_uom_id    
                     FROM
                        product_template"""

            self.env.cr.execute(sql)
            rows = self.env.cr.fetchall()
            if rows:
                for source in rows:
                    content = "{};{};{};{};{};\r\n".format(source[0], source[1], source[2], source[3], source[4])
                    output.write(content)

            self.product_attachment_filename = wizard.stock_inventory_periode_id.name + ' - product_attachment.csv'
            self.product_attachment = base64.encodestring(output.getvalue())

            output = StringIO.StringIO()
            output.write("code;name;\r\n")
            sql = """SELECT 
                        code, name    
                     FROM
                        gondola"""

            self.env.cr.execute(sql)
            rows = self.env.cr.fetchall()
            if rows:
                for source in rows:
                    content = "{};{}\r\n".format(source[0], source[1])
                    output.write(content)

            self.gondola_attachment_filename = wizard.stock_inventory_periode_id.name + ' - gondola_attachment.csv'
            self.gondola_attachment = base64.encodestring(output.getvalue())

            output = StringIO.StringIO()
            output.write("site;kode_pid;sequence;article_id;theoretical_qty;real_qty;inventory_value;\r\n")
            sql = """SELECT 
                        site, kode_pid, sequence, article_id, product_theoretical_qty, product_real_qty,inventory_value 
                     FROM
                        stock_inventory_source
                     WHERE stock_inventory_periode_id={}""".format(wizard.stock_inventory_periode_id.id)

            self.env.cr.execute(sql)
            rows = self.env.cr.fetchall()
            if rows:
                for source in rows:
                    content = "{};{};{};{};{};{};{};\r\n".format(source[0], source[1], source[2], source[3], source[4], source[5], source[6])
                    output.write(content)

            self.source_attachment_filename = wizard.stock_inventory_periode_id.name + ' - source_attachment.csv'
            self.source_attachment = base64.encodestring(output.getvalue())

            output = StringIO.StringIO()
            output.write("periode_name;gondola_code;gondola_name;user_name;ean;article_id;product_name;date;step;qty1;qty2;qty3;\r\n")
            sql = """SELECT 
                        f.name as periode_name,
                        b.code as gondola_code,
                        b.name as gondola_name,
                        c.login as user_name,
                        e.ean,
                        e.article_id,
                        e.name as product_name,
                        a.date,
                        a.step,
                        a.qty1,
                        a.qty2,
                        a.qty3
                    FROM
                        stock_inventory_trans_line a 
                    LEFT JOIN stock_inventory_trans d ON  d.id = a.stock_inventory_trans_id
                    LEFT JOIN gondola b ON b.id = d.gondola_id
                    LEFT JOIN res_users c ON c.id = d.user_id
                    LEFT JOIN product_template e on e.id = a.product_id
                    LEFT JOIN stock_inventory_periode f on a.stock_inventory_periode_id = f.id
                    WHERE a.stock_inventory_periode_id = {}""".format(self.stock_inventory_periode_id.id)

            self.env.cr.execute(sql)
            rows = self.env.cr.fetchall()
            if rows:
                for source in rows:
                    content = "{};{};{};{};{};{};{};{};{};{};{};\r\n"\
                        .format(source[0], source[1],source[2],source[3],source[4],
                                source[5],source[6],source[7],source[8],source[9],source[10],source[11])
                    output.write(content)

            self.periode_trans_attachment_filename = wizard.stock_inventory_periode_id.name + ' - periode_trans_attachment.csv'
            self.periode_trans_attachment = base64.encodestring(output.getvalue())

            self.iface_generated = True

            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'export.all.data',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }

