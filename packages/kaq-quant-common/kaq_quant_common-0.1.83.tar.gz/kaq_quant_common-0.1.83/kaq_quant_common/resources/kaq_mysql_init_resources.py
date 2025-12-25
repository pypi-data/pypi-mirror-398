import traceback
from kaq_quant_common.resources.kaq_mysql_resources import KaqQuantMysqlRepository
from sqlalchemy import text


class KaqQuantMysqlInit:
    def __init__(self, host, port, user, passwd, database, charset, mysql_script_files):
        engine = KaqQuantMysqlRepository(host, port, user, passwd, database, charset).get_conn_engine()
        
        for file in mysql_script_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 创建数据库
                with engine.connect() as conn:
                    conn.execute(text(content))
            except Exception as e:
                print(f'【创建{file} - 表】失败, {str(e)} - {str(traceback.format_exc())}')
    

if __name__ == '__main__':
    pass
        