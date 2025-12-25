import sqlite3
import os
import threading
import pandas as pd


class SqliteRepository:

    def __init__(self):
        print('sqlite\'s db init ............')
        self.con = None
        self.cur = None
        self.thread_lock = threading.Lock()

    def connect(self, db_name):
        try:
            self.thread_lock.acquire(blocking=True)
            db_path = os.getcwd() + os.sep + 'kaq_binance_sqlite3_db'
            if not os.path.exists(db_path):
                os.mkdir(db_path)

            sqlite3_db = db_path + os.sep + db_name
            self.con = sqlite3.connect(sqlite3_db, check_same_thread=False)
        except Exception as e:
            print('【SqliteRepository.connect】异常', db_name, e)
        finally:
            # print('【SqliteRepository.connect】释放锁', db_name)
            self.thread_lock.release()

    def get_table_info(self, sql):
        '''
        提取表的字段
        '''
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute(sql)
            person_all = self.cur.fetchall()
            # 返回数据
            return person_all
        except Exception as e:
            self.con.rollback()
            print('【sqllite查询失败】', sql, e)
        finally:
            # print('【SqliteRepository.select_data】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    def is_table_exists(self, table_name):
        '''
        表是否存在
        '''
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute("PRAGMA table_info({})".format(table_name))
            person_all = self.cur.fetchone()
            # 返回数据
            if person_all is not None:
                return True
            else:
                return False
        except Exception as e:
            self.con.rollback()
            print('【sqllite查询失败】', table_name, e)
        finally:
            # print('【SqliteRepository.select_data】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    def close(self):
        try:
            self.thread_lock.acquire(blocking=True)
            self.con.close()
        except Exception as e:
            print('【SqliteRepository.close】异常', e)
        finally:
            # print('【SqliteRepository.close】释放锁')
            self.thread_lock.release()

    def create_table(self, create_table_sql):
        try:
            self.thread_lock.acquire(blocking=True)
            self.cur = self.con.cursor()
            self.cur.execute(create_table_sql)
            self.con.commit()
            # print('【创建表成功】', create_table_sql)
        except Exception as e:
            print('【sqllite创建表失败】', create_table_sql, e)
        finally:
            # print('【SqliteRepository.create_table】释放锁', create_table_sql)
            self.cur.close()
            self.thread_lock.release()

    def insert_tab(self, insert_sql, params):
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute(insert_sql, params)
            self.con.commit()
            # print('插入成功')
        except Exception as e:
            self.con.rollback()
            print("【sqllite插入失败】", insert_sql, params, e)
        finally:
            # print('【SqliteRepository.insert_tab】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    def delete_data(self, delete_sql, params):
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute(delete_sql, params)
            self.con.commit()
            # print('删除成功')
        except Exception as e:
            self.con.rollback()
            print('【sqllite删除失败】', e, delete_sql, params)
        finally:
            # print('【SqliteRepository.delete_data】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    def update_data(self, update_sql, params):
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute(update_sql, params)
            self.con.commit()
            # print('修改成功')
        except Exception as e:
            self.con.rollback()
            # print('【sqllite更新失败】', e, update_sql, params)
        finally:
            # print('【SqliteRepository.update_data】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    def select_data(self, select_sql, params):
        try:
            self.thread_lock.acquire(True)
            self.cur = self.con.cursor()
            self.cur.execute(select_sql, params)
            person_all = self.cur.fetchall()
            # 返回数据
            return person_all
        except Exception as e:
            self.con.rollback()
            print('【sqllite查询失败】', select_sql, params, e)
        finally:
            # print('【SqliteRepository.select_data】释放锁', params)
            self.cur.close()
            self.thread_lock.release()

    # 将pdFrame转为table
    def pd_transfer_table(self, pd_df, table_name):
        try:
            self.thread_lock.acquire(True)
            pd.io.sql.to_sql(pd_df, table_name, self.con, if_exists='replace')
        except Exception as e:
            print('将pdFrame转为table失败', e)
        finally:
            self.thread_lock.release()


sqliteRepository = SqliteRepository()


