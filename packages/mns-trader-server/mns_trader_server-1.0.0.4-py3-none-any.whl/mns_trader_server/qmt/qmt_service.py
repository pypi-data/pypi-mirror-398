import time, datetime, sys
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant
from loguru import logger
import pandas as pd
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.constant.db_name_constant as db_name_constant

from mns_trader_server.common.terminal_enum import TerminalEnum
import mk_common.component.qmt.qmt_price_api as qmt_price_api
import mns_common.component.common_service_fun_api as common_service_fun_api


# 回调信息
class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        logger.error("连接断开回调:{}", datetime.datetime.now())

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        logger.info("委托回调 投资备注:｛｝,{}", datetime.datetime.now(), order.order_remark)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        logger.info("时间:{},成交回调:｛｝,委托方向(48买 49卖):{},成交价格:{},成交数量:{}",
                    datetime.datetime.now(),
                    trade.order_remark,
                    trade.offset_flag,
                    trade.traded_price,
                    trade.traded_volume
                    )

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        msg = order_error.order_remark + order_error.error_msg
        logger.error("委托报错回调:{}", msg)

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        logger.error("撤单失败推送:{},{}", datetime.datetime.now(),
                     sys._getframe().f_code.co_name)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print(f"异步委托回调 投资备注: {response.order_remark}")

    def on_cancel_order_stock_async_response(self, response):
        """
        :param response: XtCancelOrderResponse 对象
        :return:
        """
        print(datetime.datetime.now(), sys._getframe().f_code.co_name)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print(datetime.datetime.now(), sys._getframe().f_code.co_name)


# 下单
def order_buy(symbol, buy_price, buy_volume):
    logger.warning("委托买入代码:{},买入价格:{},买入数量:{}", symbol, buy_price, buy_volume)
    xt_trader = get_xt_trader()
    acc = get_trade_acc()
    seq = xt_trader.order_stock(acc,
                                symbol,
                                xtconstant.STOCK_BUY,
                                buy_volume,
                                xtconstant.FIX_PRICE,
                                buy_price,
                                "STOCK_BUY",
                                symbol)
    result_dict = {"entrust_no": str(seq)}
    return result_dict


# 自动一键打新
def auto_ipo_buy():
    return None


# 卖出
def order_sell(symbol, sell_price, sell_volume):
    logger.warning("委托卖出代码:{},卖出价格:{},卖出数量:{}", symbol, sell_price, sell_volume)
    xt_trader = get_xt_trader()
    acc = get_trade_acc()
    seq = xt_trader.order_stock(acc,
                                symbol,
                                xtconstant.STOCK_SELL,
                                sell_volume,
                                xtconstant.FIX_PRICE,
                                sell_price,
                                "STOCK_SELL",
                                symbol)
    result_dict = {"entrust_no": str(seq)}
    return result_dict


# account_id	str	资金账号
# stock_code	str	证券代码
# volume	int	持仓数量
# can_use_volume	int	可用数量
# open_price	float	开仓价
# market_value	float	市值
# frozen_volume	int	冻结数量
# on_road_volume	int	在途股份
# yesterday_volume	int	昨夜拥股
# avg_price	float	成本价
# https://dict.thinktrader.net/nativeApi/xttrader.html#%E6%8C%81%E4%BB%93xtposition
def get_position():
    xt_trader = get_xt_trader()
    acc = get_trade_acc()
    position_list = xt_trader.query_stock_positions(acc)
    position_df = None
    for i in position_list:
        try:
            position_total_dict = {
                "account_type": i.account_type,
                "account_id": i.account_id,
                "stock_code": i.stock_code,
                "can_use_volume": i.can_use_volume,
                "open_price": i.open_price,
                "market_value": i.market_value,
                "frozen_volume": i.frozen_volume,
                "on_road_volume": i.on_road_volume,
                "yesterday_volume": i.yesterday_volume,
                "avg_price": i.avg_price
            }
            position_total_df = pd.DataFrame(position_total_dict, index=[1])
            if position_df is None:
                position_df = position_total_df
            else:
                position_df = pd.concat([position_total_df, position_df])
        except BaseException as e:
            logger.error("获取持仓信息异常:{}", e)
    position_df['profit_loss'] = round(position_df['market_value'] - (
            position_df['yesterday_volume'] * position_df['avg_price']), 2)
    return position_df


# 取消
def order_cancel(entrust_no, symbol):
    xt_trader = get_xt_trader()
    acc = get_trade_acc()
    if symbol[-2:] == 'SZ':
        market = xtconstant.SZ_MARKET
    elif symbol[-2:] == 'SH':
        market = xtconstant.SH_MARKET
    else:
        # 北交所 todo
        market = xtconstant.SH_MARKET

    # xt_trader为XtQuant API实例对象
    cancel_result = xt_trader.cancel_order_stock_sysid(acc, market, str(entrust_no))
    return cancel_result


#
# account_type	int	账号类型，参见数据字典
# account_id	str	资金账号
# stock_code	str	证券代码，例如"600000.SH"
# order_id	int	订单编号
# order_sysid	str	柜台合同编号

# order_time	int	报单时间
# order_type	int	委托类型，参见数据字典
# order_volume	int	委托数量
# price_type	int	报价类型，该字段在返回时为柜台返回类型，不等价于下单传入的price_type，枚举值不一样功能一样，参见数据字典
# price	float	委托价格

# traded_volume	int	成交数量
# traded_price	float	成交均价
# order_status	int	委托状态，参见数据字典
# status_msg	str	委托状态描述，如废单原因
# strategy_name	str	策略名称

# order_remark	str	委托备注，最大 24 个英文字符
# direction	int	多空方向，股票不适用；参见数据字典
# offset_flag	int	交易操作，用此字段区分股票买卖，期货开、平仓，期权买卖等；参见数据字典


# order_status todo
# xtconstant.ORDER_UNREPORTED	48	未报
# xtconstant.ORDER_WAIT_REPORTING	49	待报
# xtconstant.ORDER_REPORTED	50	已报
# xtconstant.ORDER_REPORTED_CANCEL	51	已报待撤
# xtconstant.ORDER_PARTSUCC_CANCEL	52	部成待撤
# xtconstant.ORDER_PART_CANCEL	53	部撤（已经有一部分成交，剩下的已经撤单）
# xtconstant.ORDER_CANCELED	54	已撤
# xtconstant.ORDER_PART_SUC 55	部成（已经有一部分成交，剩下的待成交）
# xtconstant.ORDER_SUCCEEDED	56	已成
# xtconstant.ORDER_JUNK	57	废单
# xtconstant.ORDER_UNKNOWN	255	未知
# 查询委托
def query_stock_orders():
    xt_trader = get_xt_trader()
    stock_account_info_df = get_account()
    account_no = list(stock_account_info_df['account'])[0]
    account = StockAccount(account_no)
    orders = xt_trader.query_stock_orders(account, False)
    order_list_df = None
    for order in orders:

        try:
            order_dict = {
                "account_type": order.account_type,
                "account_id": order.account_id,
                "stock_code": order.stock_code,
                "order_id": order.order_id,
                "order_sysid": order.order_sysid,
                "order_time": order.order_time,
                "order_type": order.order_type,
                "order_volume": order.order_volume,
                "price_type": order.price_type,
                "price": order.price,

                "traded_volume": order.traded_volume,
                "traded_price": order.traded_price,
                "order_status": order.order_status,
                "status_msg": order.status_msg,
                "strategy_name": order.strategy_name,

                "order_remark": order.order_remark,
                "direction": order.direction,
                "offset_flag": order.offset_flag,

            }

            order_df = pd.DataFrame(order_dict, index=[1])
            if order_list_df is None:
                order_list_df = order_df
            else:
                order_list_df = pd.concat([order_df, order_list_df])

        except BaseException as e:
            logger.error("获取委托信息异常:{}", e)

    return order_list_df


@lru_cache(maxsize=None)
def get_account():
    query = {'type': TerminalEnum.QMT.terminal_code}
    stock_account_info_df = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    return stock_account_info_df


# 获取账号信息
@lru_cache(maxsize=None)
def get_trade_acc():
    stock_account_info_df = get_account()
    account_no = list(stock_account_info_df['account'])[0]
    # 创建资金账号为 account_no 的证券账号对象 股票账号为STOCK 信用CREDIT 期货FUTURE
    acc = StockAccount(account_no, 'STOCK')
    return acc


# 获取连接对象
@lru_cache(maxsize=None)
def get_xt_trader():
    session_id = int(time.time())
    query = {'type': TerminalEnum.QMT.terminal_code}
    stock_account_info_df = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    data_path = list(stock_account_info_df['data_path'])[0]
    xt_trader = XtQuantTrader(data_path, session_id)

    # 创建交易回调类对象，并声明接收回调
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    # 启动交易线程
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    if connect_result == 0:
        logger.info("建立交易连接成功")
    else:
        logger.error("建立交易连接失败")
    return xt_trader


# 获取qmt交易价格
def get_qmt_trade_price(symbol, price_code, limit_chg):
    return qmt_price_api.get_qmt_trade_price(common_service_fun_api.add_after_prefix_one(symbol),
                                             price_code, limit_chg)


def get_balance():
    return {}


# adjust_stock("871753")
# from xtquant import xtdata

if __name__ == '__main__':
    query_stock_orders()
    pass
    # order_buy('600759.SH', 2.82, 100)
#     logger.info(get_position())
#     trade_no = order_sell('600383.SH', 3.27, 100)
#     order_cancel(trade_no, '871753')
#     company_df = mongodb_util.find_all_data(db_name_constant.COMPANY_INFO)
#     symbol_list = list(company_df['_id'])
#     full_tick = xtdata.get_full_tick(['300085.SZ'])
#     print(full_tick)
