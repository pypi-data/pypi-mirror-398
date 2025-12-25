import threading
import traceback
from string import Template

import dolphindb as ddb
from kaq_quant_common.utils import yml_utils
from kaq_quant_common.utils.logger_utils import get_logger

mutex = threading.Lock()


class KaqQuantDdbStreamInitRepository:
    '''
    定义 asof_join的级联方式, 合并数据到一起, 然后可以订阅判断
    '''

    def __init__(self, host, port, user, passwd, ddb_script_files={}):
        self.logger = get_logger(self)
        if not host or not port or not user or not passwd:
            self.logger.error("【DDB连接参数错误】请检查配置文件")
        if not ddb_script_files or len(ddb_script_files) == 0:
            self.logger.error("【DDB脚本文件列表为空】请检查配置文件")

        mutex.acquire()
        '''
        创建ddb连接 && 添加ddb流数据表支持
        '''
        self.session = ddb.session(enableASYNC=True)
        self.session.connect(host, port, user, passwd)
        self.session.enableStreaming()

        '''
        创建流数据表 && 创建引擎
        '''
        for script_file, args in ddb_script_files.items():
            try:
                # 读取脚本 并转换为gbk编码
                with open(file=script_file, mode="r", encoding="utf-8") as fp:
                    script = fp.read().encode('gbk').decode('gbk')
                if args is None or len(args) == 0:
                    # self.session.runFile(script_file)
                    pass
                else:
                    template = Template(script)
                    script = template.substitute(**args)
                self.session.run(script)
            except Exception as e:
                self.logger.error(f"【创建ddb数据流引擎】 {script_file} 错误异常: {str(e)} - {str(traceback.format_exc())}")
                self.cancel_subscribe()
        mutex.release()

    def cancel_subscribe(self, file_path=None):
        # return
        '''
        1、取消订阅
        PS: 此处不能使用python的localhost
        创建流订阅与引擎
        使用的是ddb的脚步
        传输到服务器上运行
        会调用的节点为服务器ip、port、节点名称
        '''
        if file_path is None or file_path == "":
            self.logger.info("【取消订阅】请传参数file_path")
            return
        self.session.runFile(file_path)

    def drop_streaming(self, file_path=None):
        # return
        '''
        1、取消订阅
        PS: 此处不能使用python的localhost
        创建流订阅与引擎
        使用的是ddb的脚步
        传输到服务器上运行
        会调用的节点为服务器ip、port、节点名称
        '''
        if file_path is None or file_path == "":
            self.logger.info("【取消订阅】请传参数file_path")
            return
        self.session.runFile(file_path)


if __name__ == '__main__':
    host, port, user, passwd = yml_utils.get_ddb_info(pkg_name='kaq_binance_quant')
    ddb_script_files = ['binance_volume_ddb_script.dos', 'binance_limit_order_ddb_script.dos', 'binance_premium_ddb_script.dos']
    ddb_script_files = [yml_utils.get_pkg_file(None, x) for x in ddb_script_files]
    kaq = KaqQuantDdbStreamInitRepository(host, port, user, passwd, ddb_script_files)
    # kaq.drop_streaming()
