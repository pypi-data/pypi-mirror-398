import os
import threading
import time
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from natsort import natsorted
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from kaq_quant_common.utils import hash_utils, yml_utils
from kaq_quant_common.utils.logger_utils import get_logger

mutex = threading.Lock()


def append_id(df: pd.DataFrame):
    """
    统一添加id和时间戳
    :param df:
    :return:
    """
    if df is not None and not df.empty:
        df = df.copy()
        df["id"] = df.apply(lambda i: hash_utils.generate_hash_id(i), axis=1)

        now_time = time.localtime()
        df["ctimestampe"] = pd.Timestamp(now_time.tm_year, now_time.tm_mon, now_time.tm_mday, now_time.tm_hour, now_time.tm_min, now_time.tm_sec)
    return df


class KaqQuantMysqlRepository:
    """
    获取过往一段时间的归集成交
    数据库创建语句：
    mysql -uroot -pxxxxxxxxxx -e "create database if not exists db_kaq_binance character set 'utf8mb4';"
    PS: 高并发下可能产生错误 (1205, 'Lock wait timeout exceeded; try restarting transaction. 使用`SET GLOBAL innodb_lock_wait_timeout = 3000;`调整)
    同时设置为可以读取已经提交的数据：
    SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
    SHOW VARIABLES LIKE 'autocommit';
    -- 禁用自动提交, 便于直接一次性提交
    -- SET autocommit = 0;
    """

    def __init__(self, host, port, user, passwd, database, charset="utf8mb4", pool_size=3):
        self.logger = get_logger(self)
        # 创建写入引擎数据库连接池
        self.conn_engine = create_engine(
            f"mysql+mysqldb://{user}:{passwd}@{host}:{port}/{database}?charset={charset}",
            # 连接池大小
            pool_size=pool_size,
            # 超出连接池后，允许的最大扩展数
            max_overflow=5,
            # 池中没有线程最多等待的时间（秒）
            pool_timeout=60,
            # 多久之后，连接自动断开，-1 表示不自动断开（秒）
            pool_recycle=650,
             # 启用连接前检查
            pool_pre_ping=True,
            echo=False,  # 关闭 SQL 语句日志
            echo_pool=False,  # 关闭连接池日志
        )
        # 会话工厂
        self.session_maker = sessionmaker(bind=self.conn_engine, autoflush=False)
        # todo 删掉
        self.session = self.session_maker()

    # 判断表是否存在
    def table_exists(self, table_name):
        # 从连接池获取连接
        session = self.session_maker()
        try:
            tables = session.execute(text("SHOW TABLES")).mappings().all()
            table_list = np.array([[v for _, v in table.items()] for table in tables]).flatten()
            return table_name in table_list
        except Exception as e:
            self.logger.error(f"【mysql-table_exists】异常, {table_name} - {str(e)}")
        finally:
            session.close()

    # 执行sql
    def execute_sql(self, sql, need_commit=False):
        # 从连接池获取连接
        session = self.session_maker()
        ret = None
        try:
            ret = session.execute(text(sql))
            if need_commit:
                session.commit()
        except Exception as e:
            self.logger.error(f"【mysql.execute_sql】异常, {sql} - {str(e)}")
            ret = None
            session.rollback()
        finally:
            session.close()
        return ret

    # 判断表是否存在
    def rename_table(self, table_name):
        # 从连接池获取连接
        session = self.session_maker()
        try:
            time_str = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
            sql = f"RENAME TABLE {table_name} TO {table_name}_{time_str};"
            session.execute(text(sql))
            return True
        except Exception as e:
            self.logger.error(f"【mysql-table_exists】异常, {table_name} - {str(e)}")
            return False
        finally:
            session.close()

    def get_table_size(self, table_name, database="db_kaq_binance"):
        """
        查询操作，输入查询语句
        """
        # 从连接池获取连接
        session = self.session_maker()
        try:
            # 从session中获取数据
            sql = f"""
                SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2)
                FROM information_schema.tables 
                WHERE table_name = '{table_name}' AND table_schema = '{database}'
            """
            count = session.execute(text(sql)).fetchone()[0]
            return count
        except Exception as e:
            self.logger.error(f"【mysql-fetch_data】异常, {sql} - {str(e)}")
        finally:
            session.close()
        return 0

    def get_table_list(self):
        # 从连接池获取连接
        session = self.session_maker()
        try:
            # 获取表名
            tables = (
                session.execute(
                    text(
                        "SELECT table_name, create_time FROM information_schema.tables WHERE table_schema = 'db_kaq_binance' ORDER BY create_time DESC"
                    )
                )
                .mappings()
                .all()
            )
            table_list = [table["TABLE_NAME"] for table in tables]
            table_list = list(reversed(natsorted(table_list)))
            return table_list
        except Exception as e:
            self.logger.error(f"【mysql-get_table_list】异常, - {str(e)}")
        finally:
            session.close()
        return []

    def fetch_data(self, query):
        """
        查询操作，输入查询语句
        """
        # 从连接池获取连接
        session = self.session_maker()
        try:
            # 从session中获取数据
            rows = session.execute(text(query)).mappings().all()
            df = pd.DataFrame(rows)
            return df
        except Exception as e:
            self.logger.error(f"【mysql-fetch_data】异常, {query} - {str(e)}")
        finally:
            session.close()
        return pd.DataFrame()

    def fetch_data_count(self, query):
        """
        查询操作，输入查询语句
        """
        # 从连接池获取连接
        session = self.session_maker()
        try:
            # 从session中获取数据
            count = session.execute(text(query)).fetchone()[0]
            return count
        except Exception as e:
            self.logger.error(f"【mysql-fetch_data】异常, {query} - {str(e)}")
        finally:
            session.close()
        return 0

    def get_conn_engine(self):
        """
        create_engine: pandas写入支持的比较好
        """
        return self.conn_engine

    def get_exits_id_list(self, df, table_name):
        """
        获取已经存在的id的列表
        """
        if df is None or df.empty:
            return []
        id_list_str = ", ".join(["'" + _id + "'" for _id in df["id"].values.tolist()])
        id_df = self.fetch_data(f"select id from {table_name} where id in ({id_list_str})")
        exits_id_list = id_df["id"].values.tolist()
        return exits_id_list

    def insert_data(self, df, table_name):
        # 将pdFrame转为table, 并存入mysql
        session = None
        try:
            mutex.acquire(True)
            if df is None or df.empty:
                return
            if "id" not in df:
                df = append_id(df)
            # df = df[~df['id'].isin(self.get_exits_id_list(df, table_name))]
            # pandas写法
            # pd.io.sql.to_sql(df, table_name, self.conn_engine, if_exists='append', index=False, chunksize=100000)

            # 使用 INSERT IGNORE, 如果遇见重复的主键id，则跳过
            columns = ", ".join([_col for _col in df.columns.values])

            # mysql默认一次性可以写入16mb数据，如果超过16mb，有可能阻塞，所以设置为1000条，应该没有问题
            mysql_max_allowed_packet = 300
            total_rows = df.shape[0]
            # 要切分的份数
            part_rows = total_rows // mysql_max_allowed_packet
            if total_rows % mysql_max_allowed_packet > 0:
                part_rows = part_rows + 1
            for i in range(part_rows):
                df_part = df.iloc[i * mysql_max_allowed_packet : (i + 1) * mysql_max_allowed_packet]

                # 拼接插入的sql语句
                value_list = ["(" + ", ".join(["'" + str(_r) + "'" for _r in row.values]) + ")" for index, row in df_part.iterrows()]
                value_list_str = ", ".join(value_list)
                query = f"INSERT IGNORE INTO {table_name} ({columns}) VALUES {value_list_str} ;"
                # 从连接池获取session
                if session is None:
                    session = self.session_maker()
                session.execute(text(query))
            # 一并提交
            if session is not None:
                session.commit()
        except Exception as e:
            self.logger.error(f"【mysql-insert_data异常】- {str(e)} - {str(traceback.format_exc())}")
            if session is not None:
                session.rollback()
        finally:
            mutex.release()
            if session is not None:
                session.close()

    def insert_data_duplicate(self, df, table_name, update_columns: list = None, mysql_max_allowed_packet = 300):
        """
        插入数据，如果遇见主键冲突，则更新指定的列
        """
        session = None
        try:
            mutex.acquire(True)
            if df is None or df.empty:
                return
            if "id" not in df:
                df = append_id(df)
            # pandas写法
            # pd.io.sql.to_sql(df, table_name, self.conn_engine, if_exists='append', index=False, chunksize=100000)

            # 使用 INSERT ... ON DUPLICATE KEY UPDATE, 如果遇见重复的主键id，则更新指定的列
            columns = ", ".join([_col for _col in df.columns.values])
            update_columns_str = ", ".join([f"{col}=IFNULL(VALUES({col}), {col})" for col in update_columns])

            # mysql默认一次性可以写入16mb数据，如果超过16mb，有可能阻塞，所以设置为1000条，应该没有问题
            
            total_rows = df.shape[0]
            # 要切分的份数
            part_rows = total_rows // mysql_max_allowed_packet
            if total_rows % mysql_max_allowed_packet > 0:
                part_rows = part_rows + 1
            for i in range(part_rows):
                df_part = df.iloc[i * mysql_max_allowed_packet : (i + 1) * mysql_max_allowed_packet]

                # 拼接插入的sql语句
                value_list = ["(" + ", ".join(["'" + str(_r) + "'" if str(_r) != 'NaT' and str(_r) != 'nan' else "NULL" for _r in row.values]) + ")" for index, row in df_part.iterrows()]
                value_list_str = ", ".join(value_list)
                query = f"INSERT INTO {table_name} ({columns}) VALUES {value_list_str} ON DUPLICATE KEY UPDATE {update_columns_str} ;"

                # 从连接池获取session
                if session is None:
                    session = self.session_maker()
                session.execute(text(query))
            # 一并提交
            if session is not None:
                session.commit()
        except Exception as e:
            self.logger.error(f"【mysql-insert_data_duplicate异常】- {str(e)} - {str(traceback.format_exc())}")
            if session is not None:
                session.rollback()
        finally:
            mutex.release()
            if session is not None:
                session.close()


def main(query="select * from kaq_binance_perpetual_klines_1h limit 5;"):
    host, port, user, passwd, database, charset = yml_utils.get_mysql_info(os.getcwd())
    KaqQuantMysqlRepository = KaqQuantMysqlRepository(host, port, user, passwd, database, charset)

    print(KaqQuantMysqlRepository.table_exists("kaq_binance_perpetual_klines_1h"))
    # print(KaqQuantMysqlRepository.fetch_data(query).head(3))


# 测试数据库连接池
def test_db_pool():
    host, port, user, passwd, database, charset = yml_utils.get_mysql_info(os.getcwd())
    KaqQuantMysqlRepository = KaqQuantMysqlRepository(host, port, user, passwd, database, charset)

    # 获取一个session
    session1 = KaqQuantMysqlRepository.session_maker()
    session1.execute(text("SELECT 1;")).mappings().all()
    # SHOW PROCESSLIST;  有1条连接

    # 由于上面没有close,这里不会复用上面的连接
    session2 = KaqQuantMysqlRepository.session_maker()
    session2.execute(text("SELECT 1;")).mappings().all()
    # SHOW PROCESSLIST;  有2条连接

    # 关闭session
    session1.close()
    session2.close()

    # 上面session关闭后，这里再创建session会复用之前创建的连接
    session3 = KaqQuantMysqlRepository.session_maker()
    session3.execute(text("SELECT 1;")).mappings().all()
    # SHOW PROCESSLIST;  有2条连接

    print("end")


if __name__ == "__main__":
    main()
