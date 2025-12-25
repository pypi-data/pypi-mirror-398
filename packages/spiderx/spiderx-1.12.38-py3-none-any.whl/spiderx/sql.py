import sqlite3
import pymysql
class conn_sqlite3():
    def __init__(self,db_path):
        self.db_path=db_path
    def open(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
    def do_sql_execute(self,sql):
        try:
            self.cur.execute(sql)
            self.conn.commit()
            count = self.cur.rowcount
            return count
        except Exception as e:
            self.conn.rollback()
            raise Exception(e,e.__traceback__.tb_lineno)
    def do_sql_select(self,sql):
        try:
            self.cur.execute(sql)
            res=self.cur.fetchall()
            return res
        except Exception as e:
            self.conn.rollback()
            raise Exception(e,e.__traceback__.tb_lineno)
    def close(self):
        if self.conn:
            self.conn.close()
class conn_mysql():
    ''' conn=conn_mysql(host='127.0.0.1',user='root',password='123456',database='mysql') '''
    def __init__(self,host,user,password,database,port:int=3306):
        self.conn = pymysql.connect(host=host,user=user,password=password,database=database,port=port)
        self.cur = self.conn.cursor()
    def select_all(self, sql)->list:
        try:
            self.cur.execute(sql)
            res = self.cur.fetchall()
            # 返回所有记录
            return res
        except Exception as e:
            print('select_all error:', e.args)
            return []
    def select_one(self, sql)->None:
        try:
            self.cur.execute(sql)
            res = self.cur.fetchone()
            # 返回所有记录
            return res
        except Exception as e:
            print('select error:', e.args)
            return None
    def execute(self, sql)->int:
        try:
            self.cur.execute(sql)
            self.conn.commit()
            count = self.cur.rowcount
            # 返回受影响行数
            return count
        except Exception as e:
            print('execute error:', e.args)
            return 0
    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
