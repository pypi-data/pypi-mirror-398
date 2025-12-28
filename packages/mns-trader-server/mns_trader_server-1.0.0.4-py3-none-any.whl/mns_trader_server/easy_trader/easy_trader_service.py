
from loguru import logger
import easytrader
from easytrader import grid_strategies
from flask import jsonify
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from mns_trader_server.common.terminal_enum import TerminalEnum

mongodb_util = MongodbUtil('27017')
from functools import lru_cache


@lru_cache(maxsize=None)
def get_trader_user():
    query = {'type': TerminalEnum.EASY_TRADER.terminal_code}
    stock_account_info_df = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    exe_path = list(stock_account_info_df['exe_path'])[0]
    data_path = list(stock_account_info_df['data_path'])[0]
    user = easytrader.use('ths')
    user.connect(exe_path)
    user.grid_strategy = grid_strategies.Xls
    user.grid_strategy_instance.tmp_folder = data_path
    return user


# 下单
def order_buy(symbol, buy_price, buy_volume):
    user = get_trader_user()
    logger.warning("买入代码:{},买入价格:{},买入数量:{}", symbol, buy_price, buy_volume)
    user.enable_type_keys_for_editor()
    buy_result = user.buy(symbol, buy_price, buy_volume)

    return buy_result


# 自动一键打新
def auto_ipo_buy():
    user = get_trader_user()
    return user.auto_ipo()


# 获取持仓
def get_position():
    user = get_trader_user()
    result = user.position
    return jsonify(result)


# 卖出
def order_sell(symbol, sell_price, sell_volume):
    logger.warning("卖出代码:{},卖出价格:{},卖出数量:{}", symbol, sell_price, sell_volume)
    user = get_trader_user()
    user.enable_type_keys_for_editor()
    sell_result = user.sell(symbol, sell_price, sell_volume)
    return sell_result


# 取消
def order_cancel(entrust_no):
    user = get_trader_user()
    user.enable_type_keys_for_editor()
    cancel_result = user.cancel_entrust(entrust_no)
    return cancel_result


# 获取资金
def get_balance():
    user = get_trader_user()
    balance_info = user.balance
    return balance_info


if __name__ == '__main__':
    get_balance()
