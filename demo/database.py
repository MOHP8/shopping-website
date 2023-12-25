import mysql.connector

from config import Config


class Database:
    def __init__(self):
        # 获取数据库连接参数
        self.sql_host = Config.MySQL_host
        self.sql_user = Config.MySQL_user
        self.sql_password = Config.MySQL_password
        self.sql_database = Config.MySQL_database

    def connect_mysql(self):
        # 連接到MySQL資料庫
        conn = mysql.connector.connect(
            host=self.sql_host,
            user=self.sql_user,
            password=self.sql_password,
            database=self.sql_database
        )
        cursor = conn.cursor()
        return conn, cursor

    def get_data(self, select_query, params=None):
        conn, cursor = self.connect_mysql()
        cursor.execute(select_query, params)
        data = cursor.fetchall()
        return data

    def get_data_to_dict(self, select_query, params=None):
        conn, cursor = self.connect_mysql()
        cursor.execute(select_query, params)
        columns = [column[0] for column in cursor.description]
        # 將結果轉換為字典形式
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    def create_table(self, create_query):
        conn, cursor = self.connect_mysql()
        cursor.execute(create_query)

    def insert_data(self, insert_query, params=None):
        conn, cursor = self.connect_mysql()
        cursor.execute(insert_query, params)
        conn.commit()

    def update_data(self, update_query, params=None):
        conn, cursor = self.connect_mysql()
        cursor.execute(update_query, params)
        conn.commit()