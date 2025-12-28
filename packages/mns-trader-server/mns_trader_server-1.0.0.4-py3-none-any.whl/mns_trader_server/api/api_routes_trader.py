# 市场概述
from flask import Blueprint
from flask import request
import mns_trader_server.easy_trader.easy_trader_service as easy_trader_service
import mns_trader_server.qmt.qmt_service as qmt_service
from mns_trader_server.common.terminal_enum import TerminalEnum
import mns_trader_server.qmt.qmt_auto_login as qmt_auto_login
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_trader_server.qmt.qmt_real_time_api as qmt_real_time_api
import mns_trader_server.easy_trader.ths_auto_login as ths_auto_login
import mns_common.component.price.trade_price_service_api as trade_price_service_api
from flask import jsonify

api_blueprint_trader = Blueprint("api_blueprint_trader", __name__)


# 买入
@api_blueprint_trader.route('/buy', methods=['POST'])
def trade_buy():
    symbol = request.json.get("symbol")
    buy_price = request.json.get("buy_price")
    buy_volume = request.json.get("buy_volume")
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.order_buy(symbol, buy_price, buy_volume)
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_service.order_buy(symbol, buy_price, buy_volume)
    else:
        '''
        默认easy_trader
        '''
        return easy_trader_service.order_buy(symbol, buy_price, buy_volume)


# 卖出
@api_blueprint_trader.route('/sell', methods=['POST'])
def trade_sell():
    symbol = request.json.get("symbol")
    sell_price = request.json.get("sell_price")
    sell_volume = request.json.get("sell_volume")
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.order_sell(symbol, sell_price, sell_volume)
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_service.order_sell(symbol, sell_price, sell_volume)
    else:
        '''
        默认easy_trader
        '''
        return easy_trader_service.order_sell(symbol, sell_price, sell_volume)


# 自动一键打新
@api_blueprint_trader.route('/auto/ipo/buy', methods=['POST'])
def auto_ipo_buy():
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.auto_ipo_buy()
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_service.auto_ipo_buy()
    else:
        '''
        默认easy_trader
        '''
        return easy_trader_service.order_buy()


# 获取仓位
@api_blueprint_trader.route('/position', methods=['POST'])
def get_position():
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.get_position()
    elif terminal == TerminalEnum.QMT.terminal_code:
        position_df = qmt_service.get_position()
        dict_data = position_df.to_dict(orient='records')
        return jsonify(dict_data)
    else:
        '''
        默认easy_trader
        '''
        return easy_trader_service.get_position()


# 撤单
@api_blueprint_trader.route('/cancel', methods=['POST'])
def order_cancel():
    terminal = request.json.get("terminal")
    entrust_no = request.json.get("entrust_no")
    symbol = request.json.get("symbol")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.order_cancel(entrust_no)
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_service.order_cancel(entrust_no, symbol)
    else:
        '''
        默认easy_trader
        '''
        return easy_trader_service.order_cancel(entrust_no)


# 客户端自动登陆
@api_blueprint_trader.route('/auto/login', methods=['POST'])
def auto_login():
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return ths_auto_login.ths_auto_login()
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_auto_login.qmt_auto_login()


# 获取账户余额
@api_blueprint_trader.route('/account/balance', methods=['GET'])
def account_balance():
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return easy_trader_service.get_balance()
    elif terminal == TerminalEnum.QMT.terminal_code:
        return qmt_auto_login.qmt_auto_login()


# 获取交易价格
@api_blueprint_trader.route('/trade/price', methods=['POST'])
def get_trade_price():
    terminal = request.json.get("terminal")
    symbol = request.json.get("symbol")
    price_code = request.json.get("price_code")
    limit_chg = request.json.get("limit_chg")
    trade_price = 0
    if terminal == TerminalEnum.EM.terminal_code:
        trade_price = trade_price_service_api.get_trade_price(common_service_fun_api.symbol_add_prefix(symbol),
                                                              price_code, limit_chg)
    elif terminal == TerminalEnum.QMT.terminal_code:
        trade_price = qmt_service.get_qmt_trade_price(symbol, price_code, limit_chg)

    result_dict = {"trade_price": trade_price}
    return jsonify(result_dict)


# 获取qmt行情
@api_blueprint_trader.route('/qmt/real/time/quotes/detail', methods=['POST'])
def get_qmt_real_time_quotes_detail():
    terminal = request.json.get("terminal")
    symbol_list = request.json.get("symbol_list")

    if terminal == TerminalEnum.QMT.terminal_code:
        qmt_real_time_quotes_detail_df = qmt_real_time_api.get_qmt_real_time_quotes_detail(symbol_list)
        qmt_real_time_quotes_detail_list = qmt_real_time_quotes_detail_df.to_dict(orient='records')
        return jsonify(qmt_real_time_quotes_detail_list)


# 查询订单
@api_blueprint_trader.route('/order', methods=['GET'])
def query_orders():
    terminal = request.json.get("terminal")
    if terminal == TerminalEnum.EASY_TRADER.terminal_code:
        return jsonify([])
    elif terminal == TerminalEnum.QMT.terminal_code:
        stock_orders_df = qmt_service.query_stock_orders()
        stock_orders_list = stock_orders_df.to_dict(orient='records')
        return jsonify(stock_orders_list)
