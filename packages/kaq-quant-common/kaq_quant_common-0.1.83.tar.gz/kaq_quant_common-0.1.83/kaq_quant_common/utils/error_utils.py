import os

_path = os.getcwd()

'''
根据异常错误判断是否重试
'''


def retry_if_io_error(exception):
    print("【zhima_util】异常错误为", exception)
    return isinstance(exception, IOError) or isinstance(exception, OSError)

'''
这里只是为了提供一个重试的方式，不一定要执行代理方式
'''


def retry_if_env_error(exception):
    return isinstance(exception, EnvironmentError)


