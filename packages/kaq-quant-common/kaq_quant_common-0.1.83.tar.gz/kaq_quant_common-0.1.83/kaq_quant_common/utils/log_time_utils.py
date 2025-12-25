import time

from kaq_quant_common.utils import logger_utils


def log_time(start_msg:str = ""):
    """
    使用示例：
    timer = log_time("开始了吗？？？")()
    time.sleep(2)  # 模拟一些操作
    timer("测试操作完成1")  # 记录结束并输出
    time.sleep(2)  # 模拟一些操作
    timer("测试操作完成2")  # 记录结束并输出

    timer2 = log_time("开始了吗？？？")()
    time.sleep(3)
    timer2("测试操作完成3")
    """
    logger = logger_utils.get_logger()
    start = [None]

    def begin():
        start[0] = time.time()
        logger.info(f"{start_msg}[start]")
        return end
    
    def end(msg=""):
        duration = time.time() - start[0]
        logger.info(f"{start_msg}{msg}:[end] Duration {duration:.6f} 秒")
        return duration

    return begin