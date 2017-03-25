# -*- coding: utf-8 -*-

'''
功能：更新所有基金和股票的历史记录。
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
                sql_query_date = "SELECT date FROM %s ORDER BY date DESC LIMIT 1"%table_name
                conn = sqlite3.connect(SQLITE_DATABASE_URI)
                cur = conn.cursor()
                try:
                    rs = conn.execute(sql_query_date).fetchone()
                except:
                    print('查询数据库出错，无法查询表%s内容。'%table_name)
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
    
def update_fund_data():
    '''Update all fund history records to the present day.
       Fund list table: 'stock_basics'
       Single fund history table: 'fund_xxxxxx'
    Args: 
        None
    Return: 
        None
    '''
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    conn = sqlite3.connect(SQLITE_DATABASE_URI)
    cur = conn.cursor()
    sql_query_fundcode = "SELECT code FROM fund_basics"
    try:
        rows = cur.execute(sql_query_fundcode).fetchall()
        #print(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    rowcount = 1
    for row in rows:
        progress_str = '基金更新总进度：%s/%s'%(rowcount,len(rows))
        print(progress_str)
        fund_code = row
        table_name = 'fund_%s'%fund_code
        url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=%s&page=1&per=9999"%fund_code
        print('code=%s, type(code)=%s, url=%s'%(fund_code,type(fund_code),url))
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content,'lxml')
        creatime = ""
        data = ""
        list_date =[]
        list_netvalue = []
        list_cumnetvalue = []
        list_dailygrowth = []
        table = soup.find("table", {"class" : "w782 comm lsjz"})
        td_th = re.compile('t[dh]')
        for row in table.findAll("tr"):
            cells = row.findAll(td_th)
            if len(cells) == 7 and cells[0].find(text=True) != '净值日期':
                list_date.append(cells[0].find(text=True))
                list_netvalue.append(cells[1].find(text=True))
                list_cumnetvalue.append(cells[2].find(text=True))
                list_dailygrowth.append(cells[3].find(text=True))
        df = pd.DataFrame({ 'date' : list_date,
                            'netvalue' : list_netvalue,
                            'cum_netvalue' : list_cumnetvalue,
                            'dailygrowth' : list_dailygrowth })
        rowcount = rowcount + 1
        conn = sqlite3.connect(SQLITE_DATABASE_URI)
        try:
            df.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
        except sqlite3.OperationalError as error:
            print('操作Sqlite3数据库出现错误，错误信息是：%s'%error)
        else:
            print('已完成表格 %s 的更新，共 %s 条数据。'%(table_name,len(df)))
        finally:
            if conn:
                conn.close()
        #print(df)
    print('全部基金数据已经完成更新，共更新 %s 个表格。'%len(rows))
        
def get_fund_lists():
    '''Get all fund list from local file, and create/update the 'fund_basics' table.
    Args: 
        Connection of database
    Return: 
        None
    '''
    # url = 'http://fund.eastmoney.com/fund.html#os_0;isall_1;ft_|;pt_1'
    # resp = requests.get(url)
    # soup = BeautifulSoup(resp.content,'lxml')
    html = open("all_funds.html", "r")
    table = BeautifulSoup(html,'lxml')
    rows = table.find_all('tr')
    list_id = []
    list_code = []
    list_name = []
    list_netvalue = []
    list_cumnetvalue = []
    for row in rows:
        id = ''
        code = ''
        name = ''
        netvalue = ''
        cumnetvalue = ''
        soup_id = row.find("td", {"class": "xh"})
        soup_code = row.find("td", {"class": "bzdm"})
        soup_netvalue = row.find("td", {"class": "dwjz black"})
        soup_cumnetvalue = row.find("td", {"class": "ljjz black"})
        if soup_id is not None:
            id = soup_id.string
        if soup_code is not None:
            code = soup_code.string
        soup_name = row.find("a", {"href": "http://fund.eastmoney.com/%s.html"%code})
        if soup_name is not None:
            name = soup_name.string
        if soup_netvalue is not None:
            netvalue = soup_netvalue.string
        if soup_cumnetvalue is not None:
            cumnetvalue = soup_cumnetvalue.string
        if id and code and name and net_value and cum_net_value:  
            list_id.append(id)
            list_code.append(code)
            list_name.append(name)
            list_netvalue.append(netvalue)
            list_cumnetvalue.append(cumnetvalue)
    df = pd.DataFrame({ 'code' : list_code,
                        'name' : list_name,
                        'netvalue' : list_netvalue,
                        'cum_netvalue' : list_cumnetvalue })
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    conn = sqlite3.connect(SQLITE_DATABASE_URI)
    df.to_sql('fund_basics', conn, flavor='sqlite', if_exists='replace')
    if conn:
        conn.close()
    print('完成fund_basics表格的更新。')
            
if __name__ == '__main__':
    # basedir = os.path.abspath(os.path.dirname(__file__))
    # SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    # print(SQLITE_DATABASE_URI)
    # conn = sqlite3.connect(SQLITE_DATABASE_URI)
    # cur = conn.cursor()
    update_stock_data()
    get_fund_lists()
    update_fund_data()