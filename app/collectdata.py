# -*- coding: utf-8 -*-

import os
import tushare as ts
import sqlite3
import datetime
import re,requests
from bs4 import BeautifulSoup
    
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
                try:
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
                        #print(df2)
                        
                        for i in range(0,len(df2)):
                            object = df2.values[i]
                            print('object=%s'%object)
                            #df2.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                            value_str = ''
                            for i in range(0,len(object)):
                                value_str = value_str + str(object[i])
                                if i < len(object)-1:
                                    value_str = value_str + ', '
                        sql_insert = "INSERT INTO %s(date,open,close,high,low,volume,code) values (%s)"%(table_name,value_str)
                        #print('sql_insert=%s, value_str= %s'%(sql_insert,value_str))
                        try:
                            conn.execute(sql_insert)
                            conn.commit()
                            print('更新了从%s 到%s 的日线记录：共%s条记录已更新.'%(dt1_str,dtstr,len(df2)))
                        except:    
                            conn.rollback()
                            print('更新数据库错误：无法插入数据，回滚该次数据库操作。')
                    else:
                        df3 = ts.get_k_data(i, start='1990-01-01', end=dtstr)
                        sql2 = "SELECT date FROM %s"%table_name
                        rs2 = conn.execute(sql2).fetchall()
                        if len(df3) == len(rs2):
                            print('没有查询到需更新的数据。')
                        else:
                            print('表格%s的日线有缺失，需要重新下载%s条数据。'%(i, len(df3)))
                            df3.to_sql(table_name, conn, flavor='sqlite', if_exists='replace')
                except:
                    print('查询数据库出错，无法查询表%s内容。'%table_name)
        else:
            print('%s:表%s不存在，现在下载%s的全部日线数据...'%(progress_str, table_name, i))
            df2 = ts.get_k_data(i,start='1990-01-01',end=dtstr)
            df2.to_sql(table_name, conn, index=True)
            print('%s条数据已更新。'%len(df2))
        rowcount = rowcount + 1
    return
    
def update_fund_data(conn):
    url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code-%s&page=1&per=9999"%fund_code
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content,'lxml')
    creatime = ""
    data = ""
    dict_funds ={}
    table = soup.find("table", {"class" : "w782 comm lsjz"})
    td_th = re.compile('t[dh]')

    for row in table.findAll("td"):
        cells = row.findAll(td_th)
        if len(cells) == 7:
            creatime = cells[0].find(text=True)
            if not creatime:
                continue
            creatime = cells[0].find(text=True)
            data = cells[2].find(text=True)
            dict_funds[creatime] = data

def get_fund_lists():
    # url = 'http://fund.eastmoney.com/fund.html#os_0;isall_1;ft_|;pt_1'
    # resp = requests.get(url)
    # soup = BeautifulSoup(resp.content,'lxml')
    html = open("all_funds_p1.html", "r")
    table = BeautifulSoup(html,'lxml')
    rows = table.find_all('tr')
    list_fund_id = []
    list_fund_code = []
    list_fund_name = []
    list_fund_net_value = []
    list_fund_cum_net_value = []
    for row in rows:
        id = ''
        code = ''
        name = ''
        net_value = ''
        cum_net_value = ''
        soup_id = row.find("td", {"class": "xh"})
        soup_code = row.find("td", {"class": "bzdm"})
        soup_net_value = row.find("td", {"class": "dwjz black"})
        soup_cum_net_value = row.find("td", {"class": "ljjz black"})
        if soup_id is not None:
            id = soup_id.string
        if soup_code is not None:
            code = soup_code.string
        soup_name = row.find("a", {"href": "%s.html"%code})
        if soup_name is not None:
            name = soup_name.string
        if soup_net_value is not None:
            net_value = soup_net_value.string
        if soup_cum_net_value is not None:
            cum_net_value = soup_cum_net_value.string
        if id and code and name and net_value and cum_net_value:  
            list_fund_id.append(id)
            list_fund_code.append(code)
            list_fund_name.append(name)
            list_fund_net_value.append(net_value)
            list_fund_cum_net_value.append(cum_net_value)
    print('len(rows)=%s, len(list_fund_id)=%s, len(fund_code)=%s, len(name)=%s, len(net_value)=%s, len(cum_net_value)=%s'%(len(rows),len(list_fund_id),len(list_fund_code),len(list_fund_name),len(list_fund_net_value),len(list_fund_cum_net_value)))
    print('fund_id: %s'%list_fund_id)
    print('fund_code: %s'%list_fund_code)
    print('list_fund_name: %s'%list_fund_name)
    print('list_fund_net_value: %s'%list_fund_net_value)
    print('list_fund_cum_net_value: %s'%list_fund_cum_net_value)
    print(list_fund_id[197],list_fund_code[197],list_fund_name[197],list_fund_net_value[197],list_fund_cum_net_value[197])
        
            
if __name__ == '__main__':
    # basedir = os.path.abspath(os.path.dirname(__file__))
    # SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    # print(SQLITE_DATABASE_URI)
    # try:
        # conn = sqlite3.connect(SQLITE_DATABASE_URI)
        # cur = conn.cursor()
        # update_stock_data(conn)
    # finally:
        # if conn:
            # cur.close()
            # conn.close()
    get_fund_lists()        
