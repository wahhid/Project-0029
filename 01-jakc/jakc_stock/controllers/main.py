import json
import logging
import werkzeug
import werkzeug.utils
from datetime import datetime
from math import ceil

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF, ustr


_logger = logging.getLogger(__name__)


class WebsiteWarehoue(http.Controller):

    @http.route('/csv/download/sap/<int:periode_id>/', auth='user', website=True)
    def csvdownload(self, periode_id, **kw):
        return http.request.env['stock.inventory.periode']._sap_csv_download({'periode_id': periode_id})

    @http.route('/warehouse/opname/index', type='http', auth='public', csrf=False)
    def index(self):
        stock_warehouse_obj = http.request.env['stock.warehouse']
        datas = {}
        warehouses = stock_warehouse_obj.sudo().search([])
        datas.update({'warehouses': warehouses})
        return request.render('jakc_stock.warehouse_opname_index',datas)

    @http.route('/warehouse/opname/login', type='http', methods=['POST'], auth='public', csrf=False)
    def login(self, **post):
        stock_inventory_periode_obj = http.request.env['stock.inventory.periode']
        stock_warehouse_obj = http.request.env['stock.warehouse']
        res_users_obj = http.request.env['res.users']
        username = post['username']
        password = post['password']
        siteid = post['siteid']
        #Find User
        user_ids = res_users_obj.sudo().search([('login','=', username)])
        if len(user_ids) > 0:
            user = user_ids[0]
            stock_warehouse = stock_warehouse_obj.sudo().browse(int(siteid))
            print stock_warehouse
            if stock_warehouse:
                request.session['userid'] = user.id
                request.session['username'] = user.name
                request.session['password'] = password
                request.session['warehouseid'] = stock_warehouse.id
                request.session['warehousename'] = stock_warehouse.name
                datas = {}
                #Find Periode
                args = [('state', '=', 'open')]
                periodes = stock_inventory_periode_obj.sudo().search(args)
                datas.update({'periodes': periodes})
                return request.render('jakc_stock.warehouse_opname_periode_list', datas)
            else:
                datas = {}
                datas.update({'error_message': 'Login Failed'})
                warehouses = stock_warehouse_obj.sudo().search([])
                datas.update({'warehouses': warehouses})
                return request.render('jakc_stock.warehouse_opname_index', datas)
        else:
            datas = {}
            datas.update({'error_message': 'Login Failed'})
            warehouses = stock_warehouse_obj.sudo().search([])
            datas.update({'warehouses': warehouses})
            return request.render('jakc_stock.warehouse_opname_index', datas)


    @http.route('/warehouse/opname/gondola/find', type='http', methods=['POST'], auth='public' ,csrf=False)
    def gondola_find(self, **post):
        datas={}
        periode_id = post['periodeid']
        stock_warehouse_obj = http.request.env['stock.warehouse']
        stock_inventory_periode_obj = http.request.env['stock.inventory.periode']
        stock_inventory_periode = stock_inventory_periode_obj.sudo().browse(int(periode_id))
        if stock_inventory_periode:
            request.session['periodeid'] = stock_inventory_periode.id
            request.session['periodename'] = stock_inventory_periode.name
            stock_warehouse = stock_warehouse_obj.sudo().browse(request.session['warehouseid'])
            if stock_warehouse:
                gondolas = stock_warehouse.gondola_ids
                datas.update({'gondolas': gondolas})
        return request.render('jakc_stock.warehouse_opname_gondola_find', datas)

    @http.route('/warehouse/opname/gondola/result', type='http', methods=['POST'], auth='public', csrf=False)
    def gondola_result(self, **post):
        datas = {}
        stock_inventory_trans_obj = http.request.env['stock.inventory.trans']
        gondola_obj = http.request.env['gondola']

        gondola_code = post['gondolacode']
        args = [('code','=', gondola_code)]
        gondola_ids = gondola_obj.sudo().search(args)
        if len(gondola_ids) > 0:
            gondola = gondola_ids[0]
            request.session['gondolaid'] = gondola.id
            request.session['gondolaname'] = gondola.name
            args = [('stock_inventory_periode_id','=', request.session['periodeid']),('gondola_id','=', gondola.id)]
            stock_inventory_trans = stock_inventory_trans_obj.sudo().search(args)
            if stock_inventory_trans:
                request.session['transid'] = stock_inventory_trans.id
                request.session['step'] = stock_inventory_trans.step
            else:
                vals = {}
                vals.update({'stock_inventory_periode_id': request.session['periodeid']})
                vals.update({'gondola_id': gondola.id})
                vals.update({'user_id': request.session.userid})
                vals.update({'state': 'open'})
                res = stock_inventory_trans_obj.create(vals)
                request.session['transid'] = res.id
                request.session['step'] = res.step

            return request.render('jakc_stock.warehouse_opname_gondola_result', datas)
        else:
            return ""

    @http.route('/warehouse/opname/trans/product', type='http', auth='public', csrf=False)
    def trans_find(self):
        return request.render('jakc_stock.warehouse_opname_trans_product')

    @http.route('/warehouse/opname/trans/qty', type='http', auth='public', methods=['POST'], csrf=False)
    def trans_product(self, **post):
        datas = {}
        ean = post['ean']
        product_template_obj = http.request.env['product.template']
        stock_inventory_trans_line = http.request.env['stock.inventory.trans.line']
        args = [('default_code', '=', str(ean))]
        product_template = product_template_obj.sudo().search(args)
        if product_template:
            request.session['productid'] = product_template[0].id
            request.session['productname'] = product_template[0].name
            request.session['article_id'] = product_template[0].article_id
            args = [('stock_inventory_trans_id','=', request.session.transid),('gondola_id','=', request.session.gondolaid)]
            stock_inventory_trans_line_ids = stock_inventory_trans_line.search(args, order='date desc')
            if len(stock_inventory_trans_line_ids) > 0:
                _logger.info('Find Last Product')
                stock_inventory_trans_line  = stock_inventory_trans_line_ids[0]
                datas.update({'lastproduct':stock_inventory_trans_line.product_id})
            else:
                _logger.info('Last Product not found')
            return request.render('jakc_stock.warehouse_opname_trans_qty', datas)
        else:
            datas.update({'msg': 'Product not found'})
            return request.render('jakc_stock.warehouse_opname_trans_product', datas)

    @http.route('/warehouse/opname/trans/save', type='http', methods=['POST'], auth='public', csrf=False)
    def trans_save(self, **post):
        datas = {}
        qty = post['qty']
        if qty < 10000:
            stock_inventory_obj = http.request.env['stock.inventory']
            stock_inventory = stock_inventory_obj.sudo().browse(request.session['periodeid'])
            stock_inventory_trans_line_obj = http.request.env['stock.inventory.trans.line']
            #args = [('stock_inventory_trans_id','=',request.session['transid']),('product_id','=', request.session['productid'])]
            #stock_inventory_trans_line = stock_inventory_trans_line_obj.sudo().search(args)
            #if stock_inventory_trans_line:
            #    vals = {}
            #    if stock_inventory.step == '1':
            #        vals.update({'qty1': int(qty)})
            #        vals.update({'qty2': int(qty)})
            #        vals.update({'qty3': int(qty)})
            #    if stock_inventory.set == '2':
            #        vals.update({'qty2': int(qty)})
            #        vals.update({'qty3': int(qty)})
            #    if stock_inventory.set == '3':
            #        vals.update({'qty3': int(qty)})
            #    stock_inventory_trans_line.sudo().write(vals)
            #else:
            vals = {}
            vals.update({'stock_inventory_trans_id': request.session['transid']})
            vals.update({'product_id': request.session['productid']})
            vals.update({'article_id': request.session['article_id']})
            if request.session['step'] == '1':
                vals.update({'qty1': int(qty)})
                vals.update({'qty2': int(qty)})
                vals.update({'qty3': int(qty)})
            elif request.session['step'] == '2':
                vals.update({'qty2': int(qty)})
                vals.update({'qty3': int(qty)})
            elif request.session['step'] == '3':
                vals.update({'qty3': int(qty)})
            stock_inventory_trans_line_obj.sudo().create(vals)
            return request.render('jakc_stock.warehouse_opname_trans_product', datas)
        else:
            return request.render('jakc_stock.warehouse_opname_trans_product', datas)
