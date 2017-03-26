# -*- coding: utf-8 -*-

'''
功能：更新所有股票的历史记录。
说明：本功能模块**单独运行**，没有其他模块调用。需设置在系统的定期运行任务中。
版本：V1.0
作者：gzMichael
'''
    
import os
import tushare as ts
import sqlite3
import datetime
import re,requests
from bs4 import BeautifulSoup
import pandas as pd
    
def update_stock_data():
    '''Update all stock history records to the present day.
       Stock list table: 'stock_basics'
       Single stock history table: 'stock_xxxxxx'
    Args: 
        None
    Return: 
        None
    '''
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    conn = sqlite3.connect(SQLITE_DATABASE_URI)
    df = ts.get_stock_basics()
    df.to_sql('stock_basics', conn, flavor='sqlite', if_exists='replace')
    if conn:
        conn.close()
    dtnow = datetime.datetime.now()
    dtstr = dtnow.strftime('%Y-%m-%d')
    rowcount = 1
    for i in df.index:
        #查询表名
        table_name = 'stock_%s'%i
        sql_str = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"%table_name
        conn = sqlite3.connect(SQLITE_DATABASE_URI)
        cur = conn.cursor()
        try:
            rows = cur.execute(sql_str).fetchall()
        except sqlite3.OperationalError as error:
            print('操作Sqlite3数据库出现错误，错误信息是：%s'%error)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        progress_str = '股票更新总进度：%s/%s'%(rowcount,len(df))
        #如果表已经存在，插入最新数据
        if len(rows) > 0:
            for row in rows:
                print('%s:表%s已存在，正在检查更新...'%(progress_str, table_name))
                #print('len(rows)=%s, row=%s'%(len(rows),row))
                sql_query_date = "SELECT date FROM %s ORDER BY date DESC LIMIT 1"%table_name
                conn = sqlite3.connect(SQLITE_DATABASE_URI)
                cur = conn.cursor()
                try:
                    rs = conn.execute(sql_query_date).fetchone()
                except sqlite3.OperationalError:
                    df2 = ts.get_k_data('%s'%table_name)
                    print('无法查询表%s内容，重新加载历史记录。更新 %s 条记录'%(table_name,len(df2)))
                    df2.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                else:    
                    if rs is None:
                        cur.execute('DROP TABLE IF EXISTS %s'%table_name)
                        #表格没有数据，从最早日期开始查询
                        dt1_str = '1990-01-01'
                    else:    
                        lastdate_str = rs[0]
                        dt1 = datetime.datetime.strptime(lastdate_str, "%Y-%m-%d")
                        dt1 = dt1 + datetime.timedelta(days=1)
                        dt1_str = dt1.strftime("%Y-%m-%d")
                    #补充最后一条数据到今天的记录
                    df2 = ts.get_k_data(i, start=dt1_str, end=dtstr)
                    if len(df2) > 0:
                        for i in range(0,len(df2)):
                            object = df2.values[i]
                            #print('object=%s'%object)
                            #df2.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                            value_str = ''
                            for i in range(0,len(object)):
                                value_str = value_str + str(object[i])
                                if i < len(object)-1:
                                    value_str = value_str + ', '
                        sql_insert = "INSERT INTO %s(date,open,close,high,low,volume,code) values (%s)"%(table_name,value_str)
                        try:
                            conn.execute(sql_insert)
                            conn.commit()
                            print('更新了从%s 到%s 的日线记录：共%s条记录已更新.'%(dt1_str,dtstr,len(df2)))
                        except sqlite3.OperationalError as error:
                            print('更新数据库错误：无法插入数据，回滚该次数据库操作。错误信息是：%s'%error)
                            conn.rollback()
                    else:
                        df3 = ts.get_k_data(i, start='1990-01-01', end=dtstr)
                        sql2 = "SELECT date FROM %s"%table_name
                        rs2 = conn.execute(sql2).fetchall()
                        if len(df3) == len(rs2):
                            print('没有查询到需更新的数据。')
                        else:
                            print('表格%s的日线有缺失，需要重新下载%s条数据。'%(i, len(df3)))
                            df3.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
        else:
            print('%s:表%s不存在，现在下载%s的全部日线数据...'%(progress_str, table_name, i))
            df2 = ts.get_k_data(i,start='1990-01-01',end=dtstr)
            conn = sqlite3.connect(SQLITE_DATABASE_URI)
            try:
                df2.to_sql(table_name, conn, index=True)
            except:
                    print('查询数据库出错，无法查询表%s内容。'%table_name)
            else:
                print('%s条数据已更新。'%len(df2))
            finally:
                if conn:
                    conn.close()
        rowcount = rowcount + 1
    return
            
if __name__ == '__main__':
    # basedir = os.path.abspath(os.path.dirname(__file__))
    # SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    # print(SQLITE_DATABASE_URI)
    # conn = sqlite3.connect(SQLITE_DATABASE_URI)
    # cur = conn.cursor()
    update_stock_data()