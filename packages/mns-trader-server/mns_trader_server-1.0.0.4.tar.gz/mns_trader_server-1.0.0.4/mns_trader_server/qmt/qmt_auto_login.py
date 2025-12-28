

import pyautogui as pa
import pywinauto as pw
from loguru import logger

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from mns_trader_server.common.terminal_enum import TerminalEnum
import mns_common.utils.cmd_util as cmd_util
mongodb_util = MongodbUtil('27017')


def qmt_auto_login():
    query = {'type': TerminalEnum.QMT.terminal_code}
    stock_account_info_df = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    user = list(stock_account_info_df['account'])[0]
    password = list(stock_account_info_df['password'])[0]
    connect_path = list(stock_account_info_df['exe_path'])[0]
    all_process_df = cmd_util.get_all_process()
    # 查看运行的是mini qmt 还是qmt
    is_running = all_process_df.loc[all_process_df['process_name'] == 'XtMiniQmt.exe'].shape[0] > 0
    if is_running:
        logger.warning("QMT终端已经在运行中")
        return {"result": 'success'}
    else:
        app = pw.Application(backend='uia').start(connect_path, timeout=10)
        app.top_window()
        pa.typewrite(user)
        pa.hotkey('tab')
        pa.typewrite(password)
        pa.hotkey('enter')
        return {"result": 'success'}


if __name__ == '__main__':
    qmt_auto_login()
