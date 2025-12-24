import pymysql
import pandas as pd

class MySql:
    def __init__(self,host,user,password,database) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connected = False
        self.connect()
        
    def connect(self):
        if self.connected:
            return
        self.db = pymysql.connect(host=self.host,
                    user= self.user , #'root',
                    password=self.password,
                    database=self.database)
        # import sqlalchemy.engine.url as url
        # from sqlalchemy import create_engine
        # self.db  = create_engine( 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8'.format(
        #                         user=user, password=password, host=host, port=port, database=database
        #                      ), connect_args={'charset': 'utf8'}
        #                     )       
        self.connected = True
        
    def disconnect(self):
        if self.connected:
            self.db.close()
            self.connected = False

    # sql = "SELECT * FROM justest"
    def executeSQL(self,sql):
        self.connect()
        sqlStm = sql
        cursor = self.db.cursor()
        cursor.execute(sqlStm)
        results = cursor.fetchall()
        return results
    
    def createTable(self,tableName):
        pass
        # 使用 cursor() 方法创建一个游标对象 cursor
        # cursor = db.cursor()
        
        # # 使用 execute() 方法执行 SQL，如果表存在则删除
        # cursor.execute("DROP TABLE IF EXISTS EMPLOYEE")
        
        # # 使用预处理语句创建表
        # sql = """CREATE TABLE EMPLOYEE (
        #         FIRST_NAME  CHAR(20) NOT NULL,
        #         LAST_NAME  CHAR(20),
        #         AGE INT,  
        #         SEX CHAR(1),
        #         INCOME FLOAT )"""
        
        # cursor.execute(sql)
 
# 关闭数据库连接
        # db.close()
    
    def getCounts(self,tableName,condString):
        self.connect()
        cursor = self.db.cursor()
        
        # SQL语句 
        sqlStatement = f"SELECT COUNT(*)  from {tableName} where {condString}"
        try:
        # 使用 execute()  方法执行 SQL 
            cursor.execute(sqlStatement)
            data = cursor.fetchone()
            return int(data[0])
        except:
            return 0
    
    def insertRows(self,tableName,contents:list)->(bool,str):
        self.connect()
        cursor = self.db.cursor()
        inscnt = 0
        # # SQL 插入语句
        try:
            for cnt in contents:
                inscnt += 1
                values = ''
                data=[]
                fields = ','.join(cnt.keys())
                for val in cnt.values():
                    data.append(str(val))
                    
                # data = cnt.values()
                placeholders = ','.join(['%s'] * len(data))
                sqlStatement = f"""INSERT IGNORE INTO {tableName} ({fields}) VALUES ({placeholders})"""
                cursor.execute(sqlStatement,data)
        # # 提交到数据库执行
            self.db.commit()
            return True,f'insert {inscnt} rows'

        except Exception as e:
            print(str(e))
            self.db.rollback()
            # self.db.close()
            return False,str(e)

    
            
    def replaceRows(self,tableName,contents:list)->(bool,str):
        self.connect()
        cursor = self.db.cursor()
        inscnt = 0
        # # SQL 插入语句
        try:
            for cnt in contents:
                inscnt += 1
                data=[]
                values = ''
                fields = ','.join(cnt.keys())
                for val in cnt.values():
                    data.append(str(val))
                    
                # data = cnt.values()
                placeholders = ','.join(['%s'] * len(data))
                sqlStatement = f"""REPLACE INTO {tableName} ({fields}) VALUES ({placeholders})"""
                cursor.execute(sqlStatement,data)
        # # 提交到数据库执行
            self.db.commit()
            return True,f'insert {inscnt} rows'

        except Exception as e:
            print(str(e))
            self.db.rollback()
            # self.db.close()
            return False,str(e)
            
    def deleteRows(self,tableName,condString):
        self.connect()
        cursor = self.db.cursor()
        
        # # SQL 插入语句
        try:
            sqlStatement = f"DELETE FROM {tableName} WHERE {condString} "
            cursor.execute(sqlStatement)
    # # 提交到数据库执行
            self.db.commit()
            return cursor.rowcount

        except:
            self.db.rollback()
            return 0
    
    def selectRows(self,tableName,condString):
        self.connect()
        cursor = self.db.cursor()
        sqlStatement = f"SELECT *  from {tableName} where {condString}"
        cursor.execute(sqlStatement)
        results = cursor.fetchall()
        return results
    
    def executeSQL_to_df(self,sqlString)->pd.DataFrame:
        self.connect()
        data = pd.read_sql(sqlString, self.db)
        return data
  
    