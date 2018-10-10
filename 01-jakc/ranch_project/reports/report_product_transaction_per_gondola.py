from datetime import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw
import logging

_logger = logging.getLogger(__name__)


class product_transaction_per_gondola(report_sxw.rml_parse):

    def _get_stock_inventory_periode(self, id):
        stock_inventory_periode_obj = self.pool.get('stock.inventory.periode')
        return stock_inventory_periode_obj.browse(self.cr, self.uid, id)

    def _get_stock_inventory_trans(self, periode_id, gondola_id):
        trans_obj = self.pool.get('stock.inventory.trans')
        args = [('stock_inventory_periode_id','=', periode_id), ('gondola_id','=', gondola_id)]
        trans_ids = trans_obj.search(self.cr, self.uid, args)
        transs = trans_obj.browse(self.cr, self.uid, trans_ids)
        return transs

    def _get_gondola(self, gondola_id):
        strSQL = """SELECT id, code, name FROM gondola WHERE id={}""".format(gondola_id)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_gondolas(self, stock_inventory_periode_id):
        strSQL = """SELECT gondola_id as id FROM stock_inventory_trans a
                    LEFT JOIN gondola b on a.gondola_id = b.id
                    WHERE stock_inventory_periode_id={} ORDER BY b.code""".format(stock_inventory_periode_id)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_gondola_range(self, start, end):
        strSQL = """SELECT id FROM gondola WHERE code BETWEEN '{}' AND '{}' ORDER BY code""".format(start.upper(), end.upper())
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_gondola_selection(self, gondola_ids):
        _logger.info(gondola_ids)
        strSQL = """SELECT id FROM gondola WHERE id IN {}""".format(tuple(gondola_ids))
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_article_diff(self, periode_id, article_id):
        source_obj = self.pool.get('stock.inventory.source')
        args = [('stock_inventory_periode_id','=',periode_id),('article_id', '=', article_id)]
        source_ids = source_obj.search(self.cr, self.uid, args)
        if len(source_ids) > 0:
            source = source_obj.browse(self.cr, self.uid, source_ids[0])
            return source.iface_diff
        else:
            return False

    def _get_article_stock(self, periode_id, article_id):
        source_obj = self.pool.get('stock.inventory.source')
        args = [('stock_inventory_periode_id','=',periode_id),('article_id', '=', article_id)]
        source_ids = source_obj.search(self.cr, self.uid, args)
        if len(source_ids) > 0:
            source = source_obj.browse(self.cr, self.uid, source_ids[0])
            return source.product_real_qty
        else:
            return 0

    def _get_stock_inventory_trans_line(self, periode_id, gondola_id, report_category, product_ids=None):
        if report_category == '02':
            if product_ids:
                products = tuple(product_ids)
                strSQL = """SELECT a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, min(a.create_date) as mindate, b.name as product_name, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN product_template as b ON a.product_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={} AND a.product_id in {} 
                            GROUP BY a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, b.name
                            ORDER BY mindate""".format(periode_id, gondola_id, products)
            else:
                strSQL = """SELECT a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, min(a.create_date) as mindate, b.name as product_name, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN product_template as b ON a.product_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={}
                            GROUP BY a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, b.name
                            ORDER BY mindate""".format(periode_id, gondola_id)
        else:
            if product_ids:
                products = tuple(product_ids)
                strSQL = """SELECT a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, b.name as product_name, a.qty1 as qty1, a.qty2 as qty2, a.qty3 as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN product_template as b ON a.product_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={} AND a.product_id in {}
                            ORDER BY a.create_date""".format(periode_id,gondola_id,products)
            else:
                strSQL = """SELECT a.stock_inventory_trans_source_id, a.product_id, c.step, b.article_id, b.ean, b.name as product_name, a.qty1 as qty1, a.qty2 as qty2, a.qty3 as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN product_template as b ON a.product_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={}
                            ORDER BY a.create_date""".format(periode_id,gondola_id)

        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_trans_line(self, line_id):
        line_obj = self.pool.get('stock.inventory.trans.line')
        return line_obj.browse(self.cr, self.uid, line_id)

    def __init__(self, cr, uid, name, context):
        super(product_transaction_per_gondola, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_stock_inventory_periode': self._get_stock_inventory_periode,
            'get_gondola': self._get_gondola,
            'get_gondolas': self._get_gondolas,
            'get_gondola_range': self._get_gondola_range,
            'get_gondola_selection': self._get_gondola_selection,
            'get_article_diff': self._get_article_diff,
            'get_article_stock': self._get_article_stock,
            'get_stock_inventory_trans': self._get_stock_inventory_trans,
            'get_stock_inventory_trans_line': self._get_stock_inventory_trans_line,
            'get_trans_line': self._get_trans_line,
        })


class report_product_transaction_per_gondola(osv.AbstractModel):
    _name = 'report.ranch_project.report_producttransactionpergondola'
    _inherit = 'report.abstract_report'
    _template = 'ranch_project.report_producttransactionpergondola'
    _wrapped_report_class = product_transaction_per_gondola


class gondola_transaction_per_product(report_sxw.rml_parse):

    def _get_stock_inventory_periode(self, id):
        stock_inventory_periode_obj = self.pool.get('stock.inventory.periode')
        return stock_inventory_periode_obj.browse(self.cr, self.uid, id)

    def _get_stock_inventory_trans(self, periode_id, gondola_id):
        trans_obj = self.pool.get('stock.inventory.trans')
        args = [('stock_inventory_periode_id','=', periode_id), ('gondola_id','=', gondola_id)]
        trans_ids = trans_obj.search(self.cr, self.uid, args)
        transs = trans_obj.browse(self.cr, self.uid, trans_ids)
        return transs

    def _get_gondolas(self):
        strSQL = """SELECT id FROM gondola ORDER BY code"""
        self.cr.execute(strSQL)
        datas = self.cr.fetchall()
        gondolas = []
        for data in datas:
            gondolas.append(data[0])
        return gondolas

    def _get_gondola_range(self, start, end):
        strSQL = """SELECT id FROM gondola WHERE code BETWEEN '{}' AND '{}' ORDER BY code""".format(start.upper(), end.upper())
        self.cr.execute(strSQL)
        datas = self.cr.fetchall()
        gondolas = []
        for data in datas:
            gondolas.append(data[0])
        return gondolas

    def _get_gondola_selection(self, gondola_ids):
        _logger.info(gondola_ids)
        strSQL = """SELECT id FROM gondola WHERE id IN {}""".format(tuple(gondola_ids))
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_product(self, product_id):
        strSQL = """SELECT * FROM product_template WHERE id={}""".format(product_id)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_products(self, periode_id):
        strSQL = """SELECT distinct(product_id) as id FROM stock_inventory_trans_line WHERE stock_inventory_periode_id={}""".format(periode_id)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_product_selection(self, product_ids):
        strSQL = """SELECT id FROM product_template WHERE id IN {}""".format(tuple(product_ids))
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_source_by_article(self, article_id):
        source_obj = self.pool.get('stock.inventory.source')
        args = [('article_id','=', article_id)]
        source_ids = source_obj.search(self.cr, self.uid, args)
        source = source_obj.browse(self.cr, self.uid, source_ids[0])
        return source

    def _get_stock_inventory_trans_line(self, periode_id, product_id, report_category, gondola_ids=None):
        if report_category == '02':
            if gondola_ids:
                gondolas = tuple(gondola_ids)
                strSQL = """SELECT a.gondola_id, c.step, b.name as gondola_name, b.code as gondola_code, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN gondola as b ON a.gondola_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.product_id={} AND a.gondola_id in {} 
                            GROUP BY a.gondola_id, c.step, b.name, b.code
                            ORDER BY a.create_date""".format(periode_id, product_id, gondolas)
            else:
                strSQL = """SELECT a.gondola_id, c.step, b.name as gondola_name, b.code as gondola_code, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN gondola as b ON a.gondola_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.product_id={}
                            GROUP BY a.gondola_id, c.step, b.name, b.code
                            ORDER BY a.create_date""".format(periode_id, product_id)
        else:
            if gondola_ids:
                gondolas = tuple(gondola_ids)
                strSQL = """SELECT a.gondola_id, c.step, b.name as gondola_name, b.code as gondola_code, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN gondola as b ON a.gondola_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={} AND a.product_id in {} 
                            GROUP BY a.gondola_id, c.step, b.name, b.code
                            ORDER BY a.create_date""".format(periode_id,product_id,gondolas)
            else:
                strSQL = """SELECT a.gondola_id, c.step, b.name as gondola_name, b.code as gondola_code, sum(a.qty1) as qty1, sum(a.qty2) as qty2, sum(a.qty3) as qty3
                            FROM stock_inventory_trans_line as a 
                            LEFT JOIN gondola as b ON a.gondola_id = b.id 
                            LEFT JOIN stock_inventory_trans c ON a.stock_inventory_trans_id = c.id 
                            WHERE a.stock_inventory_periode_id={} AND a.gondola_id={} 
                            GROUP BY a.gondola_id, c.step, b.name, b.code
                            ORDER BY a.create_date""".format(periode_id,product_id)
        self.cr.execute(strSQL)
        data = self.cr.dictfetchall()
        return data

    def _get_trans_line(self, line_id):
        line_obj = self.pool.get('stock.inventory.trans.line')
        return line_obj.browse(self.cr, self.uid, line_id)

    def __init__(self, cr, uid, name, context):
        super(gondola_transaction_per_product, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'get_stock_inventory_periode': self._get_stock_inventory_periode,
            'get_product': self._get_product,
            'get_products': self._get_products,
            'get_product_selection': self._get_product_selection,
            'get_gondolas': self._get_gondolas,
            'get_gondola_range': self._get_gondola_range,
            'get_gondola_selection': self._get_gondola_selection,
            'get_source_by_article': self._get_source_by_article,
            'get_stock_inventory_trans': self._get_stock_inventory_trans,
            'get_stock_inventory_trans_line': self._get_stock_inventory_trans_line,
            'get_trans_line': self._get_trans_line,
        })


class report_gondola_transaction_per_product(osv.AbstractModel):
    _name = 'report.ranch_project.report_gondolatransactionperproduct'
    _inherit = 'report.abstract_report'
    _template = 'ranch_project.report_gondolatransactionperproduct'
    _wrapped_report_class = gondola_transaction_per_product