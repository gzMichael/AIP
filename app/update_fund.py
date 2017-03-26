# -*- coding: utf-8 -*-

'''
功能：更新所有基金的历史记录。
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
        #print('code=%s, type(code)=%s, url=%s'%(fund_code,type(fund_code),url))
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
        if code and name:  
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
    get_fund_lists()
    update_fund_data()