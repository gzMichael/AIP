# -*- coding: utf-8 -*-

import os
import tushare as ts
import sqlite3
import datetime
    
def update_stock_data(conn):
    '''Update all stock history records to the present day.
    Args: 
        Connection of database
    Return: 
        None
    '''
    df = ts.get_stock_basics()
    df.to_sql('stock_basics', conn, flavor='sqlite', if_exists='replace')
    dtnow = datetime.datetime.now()
    dtstr = dtnow.strftime('%Y-%m-%d')
    print(dtstr)
    rowcount = 1
    for i in df.index:
        #查询表名
        table_name = 'stock_%s'%i
        sql_str = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"%table_name
        rows = cur.execute(sql_str).fetchall()
        progress_str = '%s/%s'%(rowcount,len(df))
        #如果表已经存在，插入最新数据
        if len(rows) > 0:
            for row in rows:
                print('%s:表%s已存在，正在检查更新...'%(progress_str, table_name))
                sql_query_date = "SELECT date FROM %s ORDER BY date DESC LIMIT 1"%table_name
                rs = conn.execute(sql_query_date).fetchone()
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
                    print('更新了从%s 到%s 的日线记录：共%s条记录已更新.'%(dt1_str,dtstr,len(df2)))
                    df2.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                else:
                    df3 = ts.get_k_data(i, start='1990-01-01', end=dtstr)
                    sql2 = "SELECT date FROM %s"%table_name
                    rs2 = conn.execute(sql_query_date).fetchall()
                    if len(df3) == len(rs2):
                        print('没有查询到需更新的数据。')
                    else:
                        print('表格%s的日线有缺失，需要重新下载%s条数据。'%(i, len(df3)))
                        df3.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                        
        else:
            print('%s:表%s不存在，现在下载%s的全部日线数据...'%(progress_str, table_name, i))
            df2 = ts.get_k_data(i,start='1990-01-01',end=dtstr)
            df2.to_sql(table_name, conn, index=True)
            print('%s条数据已更新。'%len(df2))
        rowcount = rowcount + 1
    return

if __name__ == '__main__':
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    print(SQLITE_DATABASE_URI)
    try:
        conn = sqlite3.connect(SQLITE_DATABASE_URI)
        cur = conn.cursor()
        update_stock_data(conn)
    finally:
        if conn:
            cur.close()
            conn.close()
