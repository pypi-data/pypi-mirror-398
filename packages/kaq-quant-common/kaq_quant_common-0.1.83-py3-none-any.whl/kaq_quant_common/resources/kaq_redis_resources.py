import json
import os
from typing import Any, List
import pandas as pd
import redis
import threading
from kaq_quant_common.utils import yml_utils
from loguru import logger
import traceback

mutex = threading.Lock()

class KaqQuantRedisRepository:
    '''
    定义 redis操作
    '''
    def __init__(self, host='localhost', port=6379, password=None, db=0):
        '''
        redis连接池
        '''
        try:
            mutex.acquire()
            # 创建连接池
            pool = redis.ConnectionPool(host=host, port=port, db=db, password=password, max_connections=3, decode_responses=True, health_check_interval=30)

            # 共享的 Redis 客户端
            self.client = redis.StrictRedis(connection_pool=pool)
        except Exception as e:
            logger.error(f"【创建redis连接】错误异常: {str(e)} - {str(traceback.format_exc())}")
        finally:
            mutex.release()
            
    # 显式代理 Redis 常用方法
    def set(self, name: str, value: Any, ex: int = None, px: int = None, nx: bool = False, xx: bool = False):
        return self.client.set(name, value, ex, px, nx, xx)

    def get(self, name: str) -> Any:
        return self.client.get(name)

    def delete(self, *names: str) -> int:
        return self.client.delete(*names)

    def keys(self, pattern: str) -> list:
        return self.client.keys(pattern)

    def exists(self, name: str) -> bool:
        return self.client.exists(name)
    
    def lrange(self, name: str) -> pd.DataFrame:
        result = self.client.lrange(name, 0, -1)
        return pd.DataFrame([json.loads(item) for item in result]) if result else pd.DataFrame()
    
    def rpush(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        # 每次都先删除，后添加
        self.client.delete(name)
        # 自定义 JSON 序列化函数
        def timestamp_serializer(obj):
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()  # 或者返回 int(obj.timestamp()) 转换为时间戳
            raise TypeError("Type not serializable")
        if df is not None and not df.empty:
            json_data = [json.dumps(row.to_dict(), default=timestamp_serializer) for _, row in df.iterrows()]
            self.client.rpush(name, *json_data)
        return 
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        '''
        根据模糊前缀获取 Redis 中匹配的键
        :param pattern: 模糊匹配的模式，支持 * 通配符
        :return: 匹配的键列表
        '''
        try:
            # 获取匹配的键
            keys = self.client.keys(pattern)
            return keys
        except Exception as e:
            logger.error(f"获取匹配键时出错: {str(e)} - {str(traceback.format_exc())}")
            return []

    def get_values_by_pattern(self, pattern: str) -> pd.DataFrame:
        '''
        批量获取 Redis 中符合模糊前缀匹配的键对应的 JSON 数据，并构建 pandas DataFrame
        :param pattern: 模糊匹配的模式，支持 * 通配符
        :return: 返回构建的 pandas DataFrame
        '''
        try:
            # 获取所有匹配的键
            keys = self.get_keys_by_pattern(pattern)
            
            # 批量获取对应的 JSON 数据
            json_data_list = self.client.mget(keys)
            
            # 将 JSON 数据转换为字典列表
            data_list = [json.loads(data.replace("'", '"')) if data else None for data in json_data_list]
            
            # 去除为 None 的数据
            data_list = [data for data in data_list if data is not None]

            # 构建 pandas DataFrame
            df = pd.DataFrame(data_list)
            return df
        except Exception as e:
            logger.error(f"获取并转换 JSON 数据时出错: {str(e)} - {str(traceback.format_exc())}")
            return pd.DataFrame()  # 返回空 DataFrame
            
    def __getattr__(self, name):
        '''
        使得对象在没有明确调用时，能够直接调用 Redis 的方法
        '''
        return getattr(self.client, name)

if __name__ == '__main__':
    host, port, passwd = yml_utils.get_redis_info(os.getcwd())
    KaqQuantRedisRepository = KaqQuantRedisRepository(host=host, port=port, password=passwd)
    # value = KaqQuantRedisRepository.get('test')
    df = KaqQuantRedisRepository.get_values_by_pattern('kaq_binance_commision_rate_*')
    print(df)