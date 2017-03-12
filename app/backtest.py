# -*- coding: utf-8 -*-

import tushare as ts
import sqlite3
import time, datetime
from math import floor

MIN_BUY_AMOUNT = 100

def backtest(conn, stockcode, start, end, period, fund):
    '''Make a backtest of given stock code.
    Args:
        Connection: Connection of database
        Sring: the code of stock
        String: The date of start in format("%Y-%m-%d").
        String: The date of end in format("%Y-%m-%d").
        String: The period of the backtest:Monthly or Yearly.
        String: The amount of fund of investment.
    Return:
        List: btrecords: [list_date, list_datetime, list_asset, list_cash, 
                            list_holding, list_price]
        Int: Return code: 0 - normal
                          1 - start/end date error
    '''
    #init
    cur = conn.cursor()
    table_name = 'stock_%s'%stockcode
    list_date = []
    #timestamp格式
    list_datetime = []
    list_asset = []
    list_cash = []
    list_holding = []
    list_price = []
    asset = 0
    cash = 0
    holding = 0
    price = 0
    dt_start = datetime.datetime.strptime(start, "%Y-%m-%d")
    dt_end = datetime.datetime.strptime(end, "%Y-%m-%d")
    #定期增加现金的日期与月份
    day_invest = dt_start.day
    month_invest = dt_start.month
    #输入的初始日期和结束日期正常
    if dt_start <= dt_end:
        dt = dt_start
        sql_query = ("SELECT date,close FROM %s WHERE date>='%s' AND date<='%s'"
                    "ORDER BY date"%(table_name,start,end)
                    )
        index = 0
        result = cur.execute(sql_query).fetchall()
        #查询到历史数据
        if result is not None:
            #开始回测过程
            while dt <= dt_end:
                #提取当天日期
                day = dt.day
                month = dt.month
                if day == day_invest:
                    if period == 'monthly':
                        cash = cash + fund
                        asset = asset + fund
                        isnotinvested = True    
                    else:
                        if month == month_invest:
                            cash = cash + fund
                            asset = asset + fund
                            isnotinvested = True
                    needs_recorded = True
                record = result[index]
                date_record = record[0]
                dt_record = datetime.datetime.strptime(date_record,"%Y-%m-%d")
                close_record = record[1]
                #当天可交易，判断是否能买入
                if dt == dt_record:
                    #余额充足，并且入金后未购买
                    if cash >= close_record * MIN_BUY_AMOUNT and isnotinvested:
                        buyamount = floor(cash / (close_record * MIN_BUY_AMOUNT))
                        holding = holding + buyamount * MIN_BUY_AMOUNT
                        cash = cash - buyamount * close_record * MIN_BUY_AMOUNT
                        asset = cash + holding * close_record
                        #needs_recorded = True
                        isnotinvested = False
                    #记录指针下移一条
                    if index < len(result) - 1:
                        index = index + 1
                #账户当天有资金出入或有买入        
                if needs_recorded:
                    list_holding.append(holding)
                    list_cash.append(cash)
                    list_price.append(close_record)
                    list_asset.append(asset)
                    list_date.append(dt.strftime("%Y-%m-%d"))
                    list_datetime.append(time.mktime(dt.timetuple()))
                    print('%s 账户有操作！：asset=%s, cash=%s, holding=%s, price=%s'%(dt.strftime("%Y-%m-%d"),asset,cash,holding,close_record))
                #模拟往后一天
                dt = dt + datetime.timedelta(days=1)
                needs_recorded = False
        #该品种没有查询到历史行情
        else:
            while dt <= dt_end:
                day = dt.day
                month = dt.month
                if day == day_invest:
                    if period == 'monthly':
                        cash = cash + fund
                        asset = cash
                        list_holding.append(0)
                        list_cash.append(cash)
                        list_price.append(0)
                        list_asset.append(asset)
                        list_date.append(dt.strftime("%Y-%m-%d"))
                    else:
                        if month == month_invest:
                            cash = cash + fund    
                            asset = cash
                            list_holding.append(0)
                            list_cash.append(cash)
                            list_price.append(0)
                            list_asset.append(asset)
                            list_date.append(dt.strftime("%Y-%m-%d"))
                dt = dt + datetime.timedelta(days=1)
        btrecords = [list_date, list_datetime, list_asset, list_cash, list_holding, list_price]
        return btrecords, 0    
    #初始日期大于结束日期        
    else:
        return [], 1
    
if __name__ == '__main__':
    import os
    import matplotlib.pyplot as plt
    from matplotlib.dates import AutoDateLocator, DateFormatter
    from matplotlib.font_manager import FontProperties
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    try:
        conn = sqlite3.connect(SQLITE_DATABASE_URI)
        cur = conn.cursor()
        table_name = 'stock_000563'
        start = '2015-12-20'
        end = '2017-01-20'
        fund = 5000
        period = 'monthly'
        stockcode = '000002'
        btrecords,code = backtest(conn,stockcode,start,end,period,fund)
        list_date, list_datetime, list_asset, list_cash, list_holding, list_price = btrecords
        x=list_datetime
        y=list_asset
        z=list_date
        #print('x=%s, type(x)=%s'%(x,type(x)))
        #print('y=%s, type(x)=%s'%(y,type(y)))
        font = FontProperties(fname = "c:/windows/fonts/simsun.ttc", size=14) 
        plt.figure(figsize=(10, 6))
        plt.plot(x,y)
        plt.xticks(x,z,rotation=27)
        plt.xlabel(u'年月',fontproperties=font)
        plt.ylabel(u'账户资产',fontproperties=font)
        plt.title(u'定投 %s 收益情况'%stockcode,fontproperties=font)
        plt.savefig('d:/a.png')
        plt.show()
        y=list_holding
        plt.figure(figsize=(10, 6))
        plt.bar(left=x,height=y,width=1000000,align='center')
        plt.xticks(x,z,rotation=27)
        plt.xlabel(u'年月',fontproperties=font)
        plt.ylabel(u'持仓数量',fontproperties=font)
        plt.title(u'持仓标的 %s 的情况'%stockcode,fontproperties=font)
        plt.savefig('d:/b.png')
        plt.show()
    finally:
        if conn:
            cur.close()
            conn.close()