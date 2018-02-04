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

    @http.route('/csv/download/sap/<int:periode_id>/', auth='public')
    def csvdownload(self, periode_id, **kw):
        return http.request.env['stock.inventory.periode']._sap_csv_download({'periode_id': periode_id})

    @http.route('/warehouse/opname/index', type='http', auth='public', csrf=False)
    def index(self):
        request.session['islogin'] = False
        stock_warehouse_obj = http.request.env['stock.warehouse']
        datas = {}
        warehouses = stock_warehouse_obj.sudo().search([])
        datas.update({'warehouses': warehouses})
        return request.render('ranch_project.warehouse_opname_index',datas)

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
                request.session['islogin'] = True
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
                return request.render('ranch_project.warehouse_opname_periode_list', datas)
            else:
                datas = {}
                datas.update({'error_message': 'Login Failed'})
                warehouses = stock_warehouse_obj.sudo().search([])
                datas.update({'warehouses': warehouses})
                return request.render('ranch_project.warehouse_opname_index', datas)
        else:
            datas = {}
            datas.update({'error_message': 'Login Failed'})
            warehouses = stock_warehouse_obj.sudo().search([])
            datas.update({'warehouses': warehouses})
            return request.render('ranch_project.warehouse_opname_index', datas)

    @http.route('/warehouse/opname/logout', type='http', auth='public', csrf=False)
    def logout(self):
        stock_warehouse_obj = http.request.env['stock.warehouse']
        datas = {}
        warehouses = stock_warehouse_obj.sudo().search([])
        datas.update({'warehouses': warehouses})
        return request.render('ranch_project.warehouse_opname_index', datas)


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
        return request.render('ranch_project.warehouse_opname_gondola_find', datas)

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
            request.session['gondolacode'] = gondola.code
            request.session['gondolaname'] = gondola.name
            gondola.write({'state':'active'})
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
                res = stock_inventory_trans_obj.sudo().create(vals)
                request.session['transid'] = res.id
                request.session['step'] = res.step
            return request.render('ranch_project.warehouse_opname_gondola_result', datas)
        else:
            return ""

    @http.route('/warehouse/opname/trans/product', type='http', auth='public', csrf=False)
    def trans_find(self):
        datas = {}
        stock_inventory_trans_obj = http.request.env['stock.inventory.trans']
        args = [('stock_inventory_periode_id','=', request.session.periodeid),('gondola_id','=', request.session.gondolaid),]
        stock_inventory_trans = stock_inventory_trans_obj.sudo().search(args)
        if len(stock_inventory_trans.line_ids) > 0:
            stock_inventory_trans_line = stock_inventory_trans.line_ids[-1]
        else:
            stock_inventory_trans_line = False
        datas.update({'stock_inventory_trans_line': stock_inventory_trans_line})
        return request.render('ranch_project.warehouse_opname_trans_product',datas)

    @http.route('/warehouse/opname/trans/back', type='http', auth='public', csrf=False)
    def trans_back(self):
        datas = {}
        return request.render('ranch_project.warehouse_opname_trans_product', datas)

    @http.route('/warehouse/opname/trans/qty', type='http', auth='public', methods=['POST'], csrf=False)
    def trans_product(self, **post):
        datas = {}
        ean = post['ean']
        product_template_obj = http.request.env['product.template']
        stock_inventory_trans_source_obj = http.request.env['stock.inventory.source']
        stock_inventory_trans_line_obj = http.request.env['stock.inventory.trans.line']
        args = [('default_code', '=', str(ean))]
        product_template = product_template_obj.sudo().search(args)
        if product_template:
            request.session['productid'] = product_template[0].id
            request.session['productname'] = product_template[0].name
            if product_template[0].article_id:
                request.session['article_id'] = product_template[0].article_id
                stock_inventory_trans_source_ids = stock_inventory_trans_source_obj.sudo().search([('article_id','=', product_template[0].article_id)])
                if len(stock_inventory_trans_source_ids) > 0:
                    request.session['source_id'] = stock_inventory_trans_source_ids[0].id
                    if request.session['step'] != '1':
                        stock_inventory_trans_line_args = [('stock_inventory_trans_id','=', request.session['transid']),('product_id','=', product_template[0].id)]
                        stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(stock_inventory_trans_line_args)
                        if len(stock_inventory_trans_line_ids) > 0:
                            _logger.info('Collection Found')
                            datas.update({'trans_lines': stock_inventory_trans_line_ids})
                        else:
                            _logger.info('Collection not Found')
                            vals = {}
                            vals.update({'stock_inventory_trans_id': request.session['transid']})
                            vals.update({'product_id': request.session['productid']})
                            vals.update({'article_id': request.session['article_id']})
                            vals.update({'stock_inventory_trans_source_id': request.session['source_id']})
                            vals.update({'step': request.session['step']})
                            if request.session['step'] == '1':
                                vals.update({'qty1': 0})
                            elif request.session['step'] == '2':
                                vals.update({'qty1': 0})
                                vals.update({'qty2': 0})
                            result = stock_inventory_trans_line_obj.sudo().create(vals)
                            _logger.info('Create Collection Transaction')
                            #stock_inventory_trans_line_args = [('stock_inventory_trans_id', '=', request.session.transid),('product_id', '=', request.session['product_id'])]
                            #stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(stock_inventory_trans_line_args,order='date desc')
                            datas.update({'trans_lines': [result]})
                else:
                    request.session['source_id'] = False
                    _logger.info('Source Not Found')
                    if request.session['step'] != '1':
                        stock_inventory_trans_line_args = [('stock_inventory_trans_id','=', request.session['transid']),('product_id','=', product_template[0].id)]
                        stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(stock_inventory_trans_line_args)
                        if len(stock_inventory_trans_line_ids) > 0:
                            _logger.info('Collection Found')
                            datas.update({'trans_lines': stock_inventory_trans_line_ids})
                        else:
                            _logger.info('Collection not Found')
                            vals = {}
                            vals.update({'stock_inventory_trans_id': request.session['transid']})
                            vals.update({'product_id': request.session['productid']})
                            vals.update({'article_id': request.session['article_id']})
                            vals.update({'stock_inventory_trans_source_id': request.session['source_id']})
                            vals.update({'step': request.session['step']})
                            if request.session['step'] == '1':
                                vals.update({'qty1': 0})
                            elif request.session['step'] == '2':
                                vals.update({'qty1': 0})
                                vals.update({'qty2': 0})
                            result = stock_inventory_trans_line_obj.sudo().create(vals)
                            _logger.info('Create Collection Transaction')
                            #stock_inventory_trans_line_args = [('stock_inventory_trans_id', '=', request.session.transid),('product_id', '=', request.session['product_id'])]
                            #stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(stock_inventory_trans_line_args,order='date desc')
                            datas.update({'trans_lines': [result]})
            else:
                request.session['article_id'] = 'xxxxxxxxxx'

            return request.render('ranch_project.warehouse_opname_trans_qty', datas)
        else:
            datas.update({'msg': 'Product not found'})
            return request.render('ranch_project.warehouse_opname_trans_product', datas)

    @http.route('/warehouse/opname/trans/save', type='http', methods=['POST'], auth='public', csrf=False)
    def trans_save(self, **post):
        stock_inventory_obj = http.request.env['stock.inventory']
        stock_inventory = stock_inventory_obj.sudo().browse(request.session['periodeid'])
        stock_inventory_trans_line_obj = http.request.env['stock.inventory.trans.line']
        datas = {}
        _logger.info(post)
        allow_process = False
        if request.session['step'] == '1':
            qty = float(post['qty'])
            if qty < 10000.0:
                allow_process = True;
        else:
            for key in post.keys():
                if float(post.get(key)) < 10000.0:
                    allow_process = True
                else:
                    allow_process = False

        if allow_process:
            if request.session['step'] == '1':
                vals = {}
                vals.update({'stock_inventory_trans_id': request.session['transid']})
                vals.update({'product_id': request.session['productid']})
                vals.update({'article_id': request.session['article_id']})
                vals.update({'stock_inventory_trans_source_id': request.session['source_id']})
                vals.update({'step': request.session['step']})
                vals.update({'qty1': qty})
                stock_inventory_trans_line_obj.sudo().create(vals)
                #stock_inventory_trans_line = http.request.env['stock.inventory.trans.line']
                args = [('stock_inventory_trans_id', '=', request.session.transid),('gondola_id', '=', request.session.gondolaid)]
                stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(args, order='date desc')
                if len(stock_inventory_trans_line_ids) > 0:
                    _logger.info('Find Last Product')
                    stock_inventory_trans_line = stock_inventory_trans_line_ids[0]
                    request.session['lastproduct'] = stock_inventory_trans_line.product_id.name
                else:
                    _logger.info('Last Product not found')
                    request.session['lastproduct'] = 'No Product'
                return request.render('ranch_project.warehouse_opname_trans_product', datas)
            elif request.session['step'] == '2':
                for key in post.keys():
                    trans_line = stock_inventory_trans_line_obj.sudo().browse(int(key))
                    vals = {}
                    vals.update({'qty2': float(post.get(key))})
                    trans_line.write(vals)
                args = [('stock_inventory_trans_id', '=', request.session.transid),
                        ('gondola_id', '=', request.session.gondolaid)]
                stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(args, order='date desc')
                if len(stock_inventory_trans_line_ids) > 0:
                    _logger.info('Find Last Product')
                    stock_inventory_trans_line = stock_inventory_trans_line_ids[0]
                    request.session['lastproduct'] = stock_inventory_trans_line.product_id.name
                else:
                    _logger.info('Last Product not found')
                    request.session['lastproduct'] = 'No Product'
                return request.render('ranch_project.warehouse_opname_trans_product', datas)
            elif request.session['step'] == '3':
                for key in post.keys():
                    trans_line = stock_inventory_trans_line_obj.sudo().browse(int(key))
                    vals = {}
                    vals.update({'qty3': float(post.get(key))})
                    trans_line.write(vals)
                args = [('stock_inventory_trans_id', '=', request.session.transid),
                        ('gondola_id', '=', request.session.gondolaid)]
                stock_inventory_trans_line_ids = stock_inventory_trans_line_obj.sudo().search(args, order='date desc')
                if len(stock_inventory_trans_line_ids) > 0:
                    _logger.info('Find Last Product')
                    stock_inventory_trans_line = stock_inventory_trans_line_ids[0]
                    request.session['lastproduct'] = stock_inventory_trans_line.product_id.name
                else:
                    _logger.info('Last Product not found')
                    request.session['lastproduct'] = 'No Product'
                return request.render('ranch_project.warehouse_opname_trans_product', datas)
            else:
                _logger.info("QTY False")
                datas.update({'msg': 'Quantity Error 2'})
                datas.update({'trans_lines': []})
                return request.render('ranch_project.warehouse_opname_trans_qty', datas)
        else:
            _logger.info("QTY False")
            datas.update({'msg': 'Quantity Error 1'})
            datas.update({'trans_lines': []})
            return request.render('ranch_project.warehouse_opname_trans_qty', datas)

    @http.route('/warehouse/opname/trans/close', type='http', auth='public', csrf=False)
    def trans_close(self):
        datas = {}
        return request.render('ranch_project.warehouse_opname_gondola_find', datas)

