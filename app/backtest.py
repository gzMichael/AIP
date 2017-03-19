# -*- coding: utf-8 -*-
import os
import tushare as ts
import sqlite3
import time, datetime
from math import floor
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.font_manager import FontProperties

MIN_BUY_AMOUNT = 100

def backtest(conn, stockcode, start, end, period, fund):
    '''Make a backtest of given stock code.
    Args:
        Connection: Connection of database
        Sring: the code of stock
        String: The date of start in format("%Y-%m-%d").
        String: The date of end in format("%Y-%m-%d").
        String: The period of the backtest:Monthly or Yearly.
        Int: The amount of fund of investment.
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
        sql_query = ("SELECT date,close FROM %s WHERE date>='%s' AND date<='%s' "
                    "ORDER BY date"%(table_name,start,end)
                    )
        index = 0
        result = cur.execute(sql_query).fetchall()
        print('sql=%s, result=%s, len(result)=%s'%(sql_query, result, len(result)))
        #查询到历史数据
        if len(result) > 0:
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
                    #print('%s 账户有操作！：asset=%s, cash=%s, holding=%s, price=%s'%(dt.strftime("%Y-%m-%d"),asset,cash,holding,close_record))
                #模拟往后一天
                dt = dt + datetime.timedelta(days=1)
                needs_recorded = False
        #该品种没有查询到历史行情，只能定期存入现金
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
                        list_date.append(dt.strftime("%y-%m"))
                        list_datetime.append(time.mktime(dt.timetuple()))
                    else:
                        if month == month_invest:
                            cash = cash + fund    
                            asset = cash
                            list_holding.append(0)
                            list_cash.append(cash)
                            list_price.append(0)
                            list_asset.append(asset)
                            list_date.append(dt.strftime("%y-%m"))
                            list_datetime.append(time.mktime(dt.timetuple()))
                dt = dt + datetime.timedelta(days=1)
        btrecords = [list_date, list_datetime, list_asset, list_cash, list_holding, list_price]
        error_str = ''
        rscode = 0
        return btrecords, error_str, rscode
    #初始日期大于结束日期
    else:
        btrecords = []
        error_str = '初始日期大于结束日期'
        rscode = 1
        return btrecords, error_str, rscode
    
def backtest_chart(btrecords, stockcode):
    
    try:
        list_date, list_datetime, list_asset, list_cash, list_holding, list_price = btrecords
    except:
        images = []
        error_str = '不能读取回测结果'
        rscode = 1
        return images, rscode, error_str
    else:    
        basedir = os.path.abspath(os.path.dirname(__file__))
        imagefile_dir = os.path.join(basedir, './static/')
        w = []
        x = []
        y = []
        z = []
        #X轴数据过多，需要合并来缩短显示数量
        if len(list_datetime) > 30:
            t = len(list_datetime) // 30
            for i in range(0,len(list_datetime)-1):
                if i % t == 0 :
                    w.append(list_holding[i])
                    x.append(list_datetime[i])
                    y.append(list_asset[i])
                    z.append(list_date[i])
        else:
            w = list_holding
            x = list_datetime
            y = list_asset
            z = list_date
        print('len(w)=%s, len(x)=%s, len(y)=%s, len(z)=%s'%(len(w),len(x),len(y),len(z)))
        font = FontProperties(fname = "c:/windows/fonts/simsun.ttc", size=14) 
        plt.figure(figsize=(8, 6))
        plt.plot(x,y)
        plt.xticks(x,z,rotation=55)
        plt.xlabel(u'年月',fontproperties=font)
        plt.ylabel(u'账户资产',fontproperties=font)
        plt.title(u'定投 %s 收益情况'%stockcode,fontproperties=font)
        imagefiles = []
        dt = time.mktime(datetime.datetime.now().timetuple())
        image_filename = str(dt) + '_1.png'
        image_title = '资金曲线图'
        imagefiles.append({'title':image_title, 'filename':image_filename })
        imagefile_url = imagefile_dir + image_filename
        plt.savefig(imagefile_url)
        #plt.show()
        plt.figure(figsize=(8, 6))
        plt.bar(left=x,height=w,width=1000000,align='center')
        plt.xticks(x,z,rotation=55)
        plt.xlabel(u'年月',fontproperties=font)
        plt.ylabel(u'持仓数量',fontproperties=font)
        plt.title(u'持仓标的 %s 的情况'%stockcode,fontproperties=font)
        image_filename = str(dt) + '_2.png'
        image_title = '持仓变化图'
        imagefiles.append({'title':image_title, 'filename':image_filename })
        imagefile_url = imagefile_dir + image_filename
        plt.savefig(imagefile_url)
        #plt.show()
        error_str = ''
        rscode = 0
        return imagefiles, error_str, rscode
    
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
        start = '2000-12-01'
        end = '2003-02-2'
        fund = 5000
        period = 'monthly'
        stockcode = '000002'
        table_name = 'stock_%s'%stockcode
        btrecords, error_str, rscode = backtest(conn,stockcode,start,end,period,fund)
        if rscode == 0:
            images, error_str, ret = backtest_chart(btrecords, stockcode)
            if ret != 0:
                print(error_str)
        else:
            print(error_str)
    finally:
        if cur:
            cur.close()
        if conn:            
            conn.close()