import os
from pathlib import Path
import yaml
import pkgutil
import importlib.resources as resources
from loguru import logger


def read_config(pkg_name='kaq_quant_common'):
    config_path = pkgutil.get_data(pkg_name, f'config{os.sep}config.yaml')
    data = yaml.load(config_path, Loader=yaml.FullLoader)
    return data

def get(pkg_name='kaq_quant_common', *args):
    '''
    根据key获取配置，支持:
    - 单个值: get_by_key('mysql', 'host') → 获取 kaq.mysql.host
    - 多个值: get_by_key('mysql', ['host', 'port']) → 获取 (kaq.mysql.host, kaq.mysql.port)
    - 多层级: get_by_key('a', 'b', 'c') → 获取 kaq.a.b.c
    - 顶层多个值: get_by_key(['api_key', 'api_secret']) → 获取 (kaq.api_key, kaq.api_secret)
    '''
    if not args:  # 没有提供key参数
        return None
    data = read_config(pkg_name)
    if data is None or 'kaq' not in data:
        return None
    data = data['kaq']  # 已定位到kaq节点
    
    last_arg = args[-1]
    if isinstance(last_arg, list):
        # 最后一个参数是列表，获取多个key的值
        keys = last_arg
        path_parts = args[:-1]  # 路径部分
        if not keys:  # 列表为空
            return None
        
        # 遍历路径部分
        current_data = data
        for part in path_parts:
            if not isinstance(current_data, dict) or part not in current_data:
                return None
            current_data = current_data[part]
        
        # 检查并获取所有key的值
        for key in keys:
            if key not in current_data:
                return None
        return tuple(current_data[key] for key in keys)
    else:
        # 所有参数均为路径，获取单个值
        current_data = data
        for part in args:
            if not isinstance(current_data, dict) or part not in current_data:
                return None
            current_data = current_data[part]
        return current_data

def get_path_file(_path=Path(__file__).parent, file_name='config.yaml', key_levels:list=['kaq', 'SECRET_KEY']):
    if file_name is None:
        logger.error('yml_utils.get_path_file file_name is None')
        return None
    config_path = f'{_path}{os.sep}{file_name}'
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if config is None:
        return None
    
    for key in key_levels:
        if isinstance(config, dict) and key in config:
            config = config[key]
    if not isinstance(config, str) and not isinstance(config, int) and not isinstance(config, float):
        return None
    return config
 


def get_spot_list(pkg_name='kaq_quant_common'):
    '''
    获取合约对应的现货列表
    '''
    return get(pkg_name, 'spot_list')

def get_future_list(pkg_name='kaq_quant_common'):
    '''
    获取合约的symbol列表
    '''
    return get(pkg_name, 'future_list')

def get_api_key_secret(pkg_name='kaq_quant_common'):
    '''
    获取api_key,api_secret
    '''
    return get(pkg_name, ['api_key','api_secret']) 

def get_proxies(pkg_name='kaq_quant_common'):
    '''
    获取代理配置
    '''
    return get(pkg_name, 'proxies')

def get_mysql_info(pkg_name='kaq_quant_common'):
    '''
    mysql配置
    '''
    return get(pkg_name, 'mysql', ['host', 'port', 'user', 'passwd', 'database', 'charset'])

def get_redis_info(pkg_name='kaq_quant_common'):
    '''
    redis配置
    '''
    return get(pkg_name, 'redis', ['host', 'port', 'passwd'])

def get_posgresql_info(pkg_name='kaq_quant_common'):
    '''
    posgresql配置
    '''
    return get(pkg_name, 'posgresql', ['host', 'port', 'user', 'passwd', 'database', 'charset'])

def get_mysql_table_prefix(pkg_name='kaq_quant_common'):
    return get(pkg_name, 'mysql_table_prefix')

def get_ddb_info(pkg_name='kaq_quant_common'):
    '''
    ddb配置
    '''
    return get(pkg_name, 'ddb', ['host', 'port', 'user', 'passwd'])

def get_pkg_file(pkg=None, file_name=''):
    if pkg is None:
        logger.error('yml_utils.get_pkg_script pkg is None')
        return None
    '''
    读取文件
    '''
    with resources.path(pkg, file_name) as file_path:
        # file_path 是一个 Path 对象, 输出文件的绝对路径
        config_path = str(file_path)
    if os.path.exists(config_path):
        return config_path
    logger.error(f'yml_utils.get_pkg_script {config_path} is not exits!')
    return None
 

 
if __name__ == '__main__':
    kv = get_ddb_info()
    print(kv)

