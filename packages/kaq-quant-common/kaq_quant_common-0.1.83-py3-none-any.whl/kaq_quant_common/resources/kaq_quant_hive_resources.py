from pyhive import hive
import pandas as pd

class KaqQuantHiveClient:
    def __init__(self, host="localhost", port=10000, username="hive", password=None, auth="NONE", database="default"):
        """
        初始化 Hive 连接
        """
        self.conn = hive.Connection(
            host=host,
            port=port,
            username=username,
            password=password,
            auth=auth,
            database=database
        )
        self.cursor = self.conn.cursor()

    def query(self, sql):
        """
        执行查询并返回结果（list of tuples）
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def query_df(self, sql):
        """
        执行查询并返回 pandas.DataFrame
        """
        return pd.read_sql(sql, self.conn)

    def insert_many(self, table, columns, values_list, partition=None):
        """
        批量插入数据
        :param table: Hive 表名
        :param columns: 插入的字段列表，如 ["id", "name", "department"]
        :param values_list: 数据列表，如 [(1, "Alice", "HR"), (2, "Bob", "IT")]
        :param partition: 可选分区，如 {"dt": "2025-09-21"}
        """
        cols = ",".join(columns)
        values_str = ",".join(
            ["(" + ",".join([f"'{str(v)}'" if isinstance(v, str) else str(v) for v in row]) + ")" 
             for row in values_list]
        )

        if partition:
            part_clause = " PARTITION (" + ",".join([f"{k}='{v}'" for k, v in partition.items()]) + ")"
        else:
            part_clause = ""

        sql = f"INSERT INTO {table}{part_clause} ({cols}) VALUES {values_str}"
        print("执行SQL:", sql)
        self.cursor.execute(sql)

    def close(self):
        """
        关闭连接
        """
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    '''
    CREATE TABLE employees (
        id INT,
        name STRING,
        position STRING,
        hire_date String
    )
    COMMENT 'Table for employee details'
    PARTITIONED BY (department STRING);

    INSERT INTO employees (id, name, position, hire_date, department) VALUES (6, 'Alice', 'Manager', '2020-05-12', 'HR');

    -- 插入第二条数据
    INSERT INTO employees (id, name, position, hire_date, department) VALUES (2, 'Bob', 'Software Engineer', '2018-11-05', 'Engineering');

    -- 插入第三条数据
    INSERT INTO employees (id, name, position, hire_date, department) VALUES (3, 'Charlie', 'Sales Representative', '2019-08-15', 'Sales');

    -- 插入第四条数据
    INSERT INTO employees (id, name, position, hire_date, department) VALUES (4, 'David', 'Data Analyst', '2021-01-22', 'Engineering');

    -- 插入第五条数据
    INSERT INTO employees (id, name, position, hire_date, department) VALUES (5, 'Eva', 'Marketing Specialist', '2020-02-17', 'Marketing');
    '''
    hive_client = KaqQuantHiveClient(
        host="127.0.0.1",
        port=10000,
        username="hive"
    )

    # 查询数据
    result = hive_client.query_df("SELECT * FROM employees")
    print(result)

    # 插入数据
    hive_client.insert_many(
        table="employees",
        columns=["id", "name", "position", "hire_date", "department"],
        values_list=[
            (101, "Alice", "Manager", "2025-09-21", "HR"),
            (102, "Bob", "Engineer", "2025-09-21", "IT")
        ],
    )

    hive_client.close()
