import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
from loguru import logger
from xtquant import xtdata


# 获取股票实时行情数据
# stockStatus 0 新股  7 停牌 5 正常交易
# askPrice 是卖价
# bidPrice 是买价
def get_qmt_real_time_quotes(symbol_list):
    try:
        res = xtdata.get_full_tick(symbol_list)
        records = []
        for symbol, stock_data in res.items():
            record = stock_data.copy()  # 创建字典副本避免修改原始数据
            record['symbol'] = symbol  # 添加股票代码列
            records.append(record)  # 添加到列表
        # 一次性转换为DataFrame
        real_time_quotes_df = pd.DataFrame(records)
        return real_time_quotes_df
    except BaseException as e:
        logger.error("获取实时行情出现异常:{}", e)
        return pd.DataFrame()


def get_qmt_real_time_quotes_detail(symbol_list):
    real_time_quotes_df = get_qmt_real_time_quotes(symbol_list)
    real_time_quotes_df['chg'] = round((real_time_quotes_df['lastPrice'] / real_time_quotes_df['lastClose'] - 1) * 100,
                                       2)
    real_time_quotes_df = calculate_buy_sell_amount(real_time_quotes_df)
    return real_time_quotes_df


def calculate_buy_sell_amount(stock_df):
    stock_df['total_sell_amount'] = stock_df.apply(
        lambda row: sum([askPrice * askVol for askPrice, askVol in zip(row['askPrice'], row['askVol'])]),
        axis=1
    )

    # 计算买入总量 (bidPrice * bidVol)
    stock_df['total_buy_amount'] = stock_df.apply(
        lambda row: sum([bidPrice * bidVol for bidPrice, bidVol in zip(row['bidPrice'], row['bidVol'])]),
        axis=1
    )

    stock_df['total_sell_amount'] = round(stock_df['total_sell_amount'] * 100, 2)
    stock_df['total_buy_amount'] = round(stock_df['total_buy_amount'] * 100, 2)
    stock_df['is_zt'] = False
    stock_df.loc[(stock_df['total_sell_amount'] == 0) & (stock_df['chg'] != 0), 'is_zt'] = True

    stock_df['is_dt'] = False
    stock_df.loc[(stock_df['total_buy_amount'] == 0) & (stock_df['chg'] != 0), 'is_dt'] = True

    return stock_df


if __name__ == '__main__':

    while True:
        symbol_one_test = ['301181.SZ']
        df = get_qmt_real_time_quotes_detail(symbol_one_test)
        logger.info(df['askPrice'])
        df[['sell_1', 'sell_2', 'sell_3', 'sell_4', 'sell_5']] = (
            df['askPrice']
            .apply(lambda x: sorted(x))  # 排序
            .apply(pd.Series)  # 拆分
        )
        df[['buy_1', 'buy_2', 'buy_3', 'buy_4', 'buy_5']] = (
            df['bidPrice']
            .apply(pd.Series)  # 拆分
        )
        logger.info(df)
