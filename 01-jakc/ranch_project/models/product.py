from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ean = fields.Char('Ean', size=100, index=True)
    article_id = fields.Char('Article #', size=100, index=True)
    marchandise_id = fields.Char('Marchandise #', size=100, index=True)


class ProductImport(models.Model):
    _name = 'product.import'

    @api.multi
    def _get_product_by_ean(self, ean):
        product_template_obj = self.env['product.template']
        args = [('ean','=', ean)]
        product_template_ids = product_template_obj.search(args)
        if len(product_template_ids) > 0:
            return product_template_ids
        else:
            return False

    @api.multi
    def trans_import(self):

        print "Process Import"
        """Load Product data from the CSV file."""
        # Decode the file data
        data = base64.b64decode(self.attachment)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)

        #if self.delimeter:
        #    delimeter = str(self.delimeter)
        #else:
        delimeter = ';'

        reader = csv.reader(file_input, delimiter=delimeter, lineterminator='\r\n')

        i = 0
        for row in reader:
            i += 1
            _logger.info(str(i))
            #print i
            #vals = {}
            #vals.update({'name': str(row[3])})
            #vals.update({'default_code': row[0]})
            #vals.update({'type': 'product'})
            #vals.update({'categ_id': 1})
            #vals.update({'article_id': row[1]})
            #vals.update({'uom_id': 1})
            #vals.update({'uom_po_id': 1})
            #res = self.env['product.template'].create(vals)
            product_template = self._get_product_by_ean(str(row[0]))
            if not product_template:
                _logger.info('INSERT')
                _logger.info(row)
                strsql = """INSERT INTO product_template (
                            name,
                            ean,
                            type,
                            categ_id,
                            marchandise_id,
                            article_id,
                            uom_id,
                            uom_po_id, 
                            tracking, 
                            active) 
                            VALUES ('{}', '{}', '{}', {}, '{}', {} ,{} , '{}', '{}', {}) RETURNING id
                        """\
                        .format(str(row[3].replace("'"," ").decode('unicode_escape').encode('ascii', 'ignore')),
                                str(row[0]),
                                'product',
                                str(1),
                                str(row[2]),
                                str(row[1]),
                                str(1),
                                str(1),
                                'none',
                                'true')
                self.env.cr.execute(strsql)

                id = self.env.cr.fetchone()[0]
                strsql = """INSERT INTO product_product(
                            product_tmpl_id, 
                            default_code,
                            active) 
                            VALUES ({},'{}',{})
                         """\
                        .format(id,
                                str(row[0]),
                                'true')
                self.env.cr.execute(strsql)
            else:
                _logger.info('UPDATE')
                _logger.info(row)
                strsql = """UPDATE product_template SET
                            name='{}',
                            ean='{}',
                            type='{}',
                            categ_id={},
                            marchandise_id='{}',
                            article_id='{}',
                            uom_id={},
                            uom_po_id={},
                            tracking='{}',
                            active={}
                            WHERE id={}
                        """\
                        .format(str(row[3].replace("'"," ").decode('unicode_escape').encode('ascii', 'ignore')),
                                str(row[0]),
                                'product',
                                str(1),
                                str(row[2]),
                                str(row[1]),
                                str(1),
                                str(1),
                                'none',
                                'true',
                                product_template[0].id)
                self.env.cr.execute(strsql)

                strsql = """UPDATE product_product SET
                            default_code='{}',
                            active={}
                            WHERE product_tmpl_id={}
                        """.format(str(row[0]),
                                   'true',
                                   product_template[0].id)
                self.env.cr.execute(strsql)

    name = fields.Date('Date')
    attachment = fields.Binary('File')
    attachment_filename = fields.Char("File Name")