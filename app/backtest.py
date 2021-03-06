# -*- coding: utf-8 -*-
import os
# import tushare as ts
import sqlite3
import time, datetime
from math import floor, pow, fabs
import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.font_manager import FontProperties
from matplotlib.pylab import date2num
from matplotlib.finance import candlestick_ohlc
import matplotlib.ticker as mticker

MIN_BUY_AMOUNT = 100

def backtest(testtype, code, start, end, period, fund):
    '''Make a backtest of given stock code.
    Args:
        Sring: the type of the test:'股票' or '基金'
        Sring: the code of stock
        String: The date of start in format("%Y-%m-%d").
        String: The date of end in format("%Y-%m-%d").
        String: The period of the backtest:Monthly or Yearly.
        Int: The amount of fund of investment.
    Return:
        List: summary of the test report
        List: Imagefiles including title and the url of the file
        Int: Return code: 0 - normal
                          1 - start/end date error
    '''
    #init
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    conn = sqlite3.connect(SQLITE_DATABASE_URI)
    cur = conn.cursor()
    if testtype == '股票':
        table_name = 'stock_%s'%code
    else:
        table_name = 'fund_%s'%code
    sql_str = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"%table_name
    #print('table_name=%s'%table_name)
    rs = None
    try:
        rs = conn.execute(sql_str).fetchone()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    if rs is not None:
        list_date = []
        list_asset = []
        list_cash = []
        list_holding = []
        list_price = []
        list_totalinvestment = []
        asset = 0
        cash = 0
        holding = 0
        price = 0
        totalinvestment = 0
        dt_start = datetime.datetime.strptime(start, "%Y-%m-%d")
        dt_end = datetime.datetime.strptime(end, "%Y-%m-%d")
        #定期增加现金的日期与月份
        day_invest = dt_start.day
        month_invest = dt_start.month
        #输入的初始日期和结束日期正常
        if dt_start <= dt_end:
            dt = dt_start
            if testtype == '股票':
                sql_query = ("SELECT date,close FROM %s WHERE date>='%s' AND date<='%s' "
                            "ORDER BY date"%(table_name,start,end)
                            )
            if testtype == '基金':
                sql_query = ("SELECT date,cum_netvalue FROM %s WHERE date>='%s' AND date<='%s' "
                            "ORDER BY date"%(table_name,start,end)
                            )
            index = 0
            result = []
            try:
                conn = sqlite3.connect(SQLITE_DATABASE_URI)
                cur = conn.cursor()
                result = cur.execute(sql_query).fetchall()
            except sqlite3.OperationalError as error:
                print('操作Sqlite3数据库出现错误，错误信息是：%s'%error)
            finally:
                if conn:
                    conn.close()
            #print('sql=%s, result=%s, len(result)=%s'%(sql_query, result, len(result)))
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
                            totalinvestment = totalinvestment + fund
                            isnotinvested = True    
                        else:
                            if month == month_invest:
                                cash = cash + fund
                                asset = asset + fund
                                totalinvestment = totalinvestment + fund
                                isnotinvested = True
                        needs_recorded = True
                    record = result[index]
                    date_record = record[0]
                    dt_record = datetime.datetime.strptime(date_record,"%Y-%m-%d")
                    close_record = float(record[1])
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
                        list_totalinvestment.append(totalinvestment)
                        list_holding.append(holding)
                        list_cash.append(cash)
                        list_price.append(close_record)
                        list_asset.append(asset)
                        list_date.append(dt.strftime("%y-%m"))
                        #print('%s 账户有操作！：asset=%s, cash=%s, holding=%s, price=%s'%(dt.strftime("%Y-%m-%d"),asset,cash,holding,close_record))
                    #模拟往后一天
                    dt = dt + datetime.timedelta(days=1)
                    needs_recorded = False
            #没有查询到该品种在给定时间段内的历史行情，报错
            else:
                # while dt <= dt_end:
                    # day = dt.day
                    # month = dt.month
                    # if day == day_invest:
                        # if period == 'monthly':
                            # cash = cash + fund
                            # asset = cash
                            # totalinvestment = totalinvestment + fund
                            # list_holding.append(0)
                            # list_cash.append(cash)
                            # list_price.append(0)
                            # list_asset.append(asset)
                            # list_date.append(dt.strftime("%y-%m"))
                            # list_totalinvestment.append(totalinvestment)
                        # else:
                            # if month == month_invest:
                                # cash = cash + fund    
                                # asset = cash
                                # totalinvestment = totalinvestment + fund
                                # list_holding.append(0)
                                # list_cash.append(cash)
                                # list_price.append(0)
                                # list_asset.append(asset)
                                # list_date.append(dt.strftime("%y-%m"))
                                # list_totalinvestment.append(totalinvestment)
                    # dt = dt + datetime.timedelta(days=1)
                error_str = '在给定的测试时段内，没有查询到该品种的行情数据。'
                rscode = 3
                summary = []
                images = []
                return summary, images, error_str, rscode
            #开始计算汇总测试结果
            if testtype == '股票':
                tname = 'stock_basics'
            if testtype == '基金':
                tname = 'fund_basics'
            conn = sqlite3.connect(SQLITE_DATABASE_URI)
            sql_str = "SELECT name FROM %s WHERE code='%s'"%(tname,code)
            stockname = conn.execute(sql_str).fetchone()
            name = ''
            if stockname:
                name = stockname[0]
            PnL = list_asset[len(list_asset)-1] - list_totalinvestment[len(list_totalinvestment)-1]
            str_PnL = str("%.2f"%PnL)
            PnL_percent = PnL / list_totalinvestment[len(list_totalinvestment)-1]
            str_PnL_percent = str("%.1f"%(PnL_percent*100)) + '%'
            yearcount = dt_end.year - dt_start.year + 1
            monthcount = (yearcount-1) * 12 + dt_end.month - dt_start.month + 1
            daycount = (dt_end - dt_start).days
            if PnL == 0:
                PnL_year = 0
                PnL_month = 0
                PnL_day = 0
            else:
                PnL_year = (pow((PnL_percent+1),1/yearcount) - 1) * 100
                PnL_month = (pow((PnL_percent+1),1/monthcount) - 1) * 100
                PnL_day = (pow((PnL_percent+1),1/daycount) - 1) * 100
                
            str_PnL_year = str("%.1f"%PnL_year) + '%'
            str_PnL_month = str("%.2f"%PnL_month) + '%'
            str_PnL_day = str("%.4f"%PnL_day) + '%'
            #汇总报告数据列表
            summary = []
            # summary[0]
            unit_data = ['测试开始时间', start]
            summary.append(unit_data)
            unit_data = ['测试结束时间', end]
            summary.append(unit_data)
            unit_data = ['代码类型', testtype]
            summary.append(unit_data)
            unit_data = ['品种代码', code]
            summary.append(unit_data)
            unit_data = ['测试品种名称', name] 
            summary.append(unit_data)
            if period == 'monthly':
                str_period = '每月'
                str_investtimes = monthcount
            else:
                str_period = '每年'
                str_investtimes = monthcount // 12
            unit_data = ['定投周期', str_period]
            summary.append(unit_data)
            unit_data = ['每周期定投金额', str('%.2f'%fund)]
            summary.append(unit_data)
            unit_data = ['投入期数', str_investtimes]
            summary.append(unit_data)
            unit_data = ['累计投入金额', str("%.2f"%totalinvestment)]
            summary.append(unit_data)
            unit_data = ['期末账户金额', str('%.2f'%asset)]
            summary.append(unit_data)
            # summary[10]
            unit_data = ['盈亏金额', str_PnL]
            summary.append(unit_data)
            unit_data = ['盈亏百分比', str_PnL_percent]
            summary.append(unit_data)
            unit_data = ['测试时长(年)', yearcount]
            summary.append(unit_data)
            unit_data = ['年化收益率(复合)', str_PnL_year]
            summary.append(unit_data)
            unit_data = ['测试时长(月)', monthcount]
            summary.append(unit_data)
            unit_data = ['月化收益率(复合)', str_PnL_month]
            summary.append(unit_data)
            unit_data = ['测试时长(日)', daycount]
            summary.append(unit_data)
            unit_data = ['日化收益率(复合)', str_PnL_day]
            summary.append(unit_data)
            error_str = ''
            rscode = 0
        #初始日期大于结束日期！
        else:
            error_str = '初始日期必须大于结束日期'
            rscode = 1
            summary = []
            images = []
            return summary, images, error_str, rscode
    else:
        error_str = '''没有查询到该品种的数据记录，请确认输入的代码/品种是否正确\n
                    如果这是数据采集的问题，请与开发者(gzMichael:1960809@qq.com)联系，谢谢！'''
        rscode = 2
        summary = []
        images = []
        return summary, images, error_str, rscode
    #******************************************************************************************
    #*****************************************开始画图*****************************************
    #******************************************************************************************
    imagefile_dir = os.path.join(basedir, './static/tmp_pic/')
    #z是X轴的坐标值显示标签
    z = []
    #X轴数据过多，X轴坐标减少显示数量
    if len(list_date) > 10:
        t = len(list_date) // 10
        for i in range(0,len(list_date)):
            if i % t == 0:
                z.append(list_date[i])
            else:
                z.append('')
    else:
        z = list_date
    w = list_holding
    y = list_asset
    y2 = list_totalinvestment
    i = 0
    j = len(y)
    yy = []
    yy2 = []
    while i < j:
        yy.append(floor(y[i]/1000))
        yy2.append(floor(y2[i]/1000))
        i+=1                      
    x = range(len(y))
    print('len(w)=%s, len(x)=%s, len(y)=%s, len(z)=%s'%(len(w),len(x),len(y),len(z)))
    #font = FontProperties(fname = "c:/windows/fonts/simsun.ttc", size=12) 
    #*****************************************图1：资金曲线图*****************************************
    plt.figure(figsize=(8, 6))
    plt.plot(x,yy,color='r',label=u'Total Asset')
    plt.plot(x,yy2,color='b',label=u'Cash Investment')
    plt.legend(loc='upper left', numpoints=1)
    leg = plt.gca().get_legend()
    ltext  = leg.get_texts()
    plt.setp(ltext, fontsize='small')
    plt.xticks(x,z,rotation=45)
    #plt.yticks(y,y2)
    #plt.xlabel(u'Date')
    plt.ylabel(u'Asset(K)')
    plt.title(u'Investment Income of %s'%code)
    plt.grid(True)
    imagefiles = []
    dt = time.mktime(datetime.datetime.now().timetuple())
    image_filename = str(dt) + '_1.png'
    image_title = u'%s：%s(%s) 回测资金曲线图'%(testtype,name,code)
    imagefiles.append({'title':image_title, 'filename':image_filename })
    imagefile_url = imagefile_dir + image_filename
    plt.savefig(imagefile_url)
    #plt.show()
    #*****************************************图2：盈亏曲线图*****************************************
    plt.figure(figsize=(8, 6))
    i = 0
    j = len(list_totalinvestment)
    y = []
    while i < j:
        y.append((list_asset[i] - list_totalinvestment[i])/1000)
        i+=1                      
    plt.plot(x,y,color='r',label=u'Profit And Loss Chart')
    plt.xticks(x,z,rotation=45)
    #plt.xlabel(u'Date')
    plt.ylabel(u'Profit(K)')
    plt.title(u'Profit and Lost Chart of %s'%code)
    plt.grid(True)
    image_filename = str(dt) + '_2.png'
    image_title = u'%s：%s(%s) 盈亏曲线图'%(testtype,name,code)
    imagefiles.append({'title':image_title, 'filename':image_filename })
    imagefile_url = imagefile_dir + image_filename
    plt.savefig(imagefile_url)
    #*****************************************图3：持仓曲线图*****************************************
    plt.figure(figsize=(8, 6))
    plt.bar(left=x,height=w,width=0.4,align='center')
    plt.xticks(x,z,rotation=45)
    #plt.xlabel(u'Date')
    plt.ylabel(u'Positions')
    plt.title(u'Changes in positions of %s'%code)
    plt.grid(True)
    image_filename = str(dt) + '_3.png'
    image_title = u'%s：%s(%s) 持仓变化图'%(testtype,name,code)
    imagefiles.append({'title':image_title, 'filename':image_filename })
    imagefile_url = imagefile_dir + image_filename
    plt.savefig(imagefile_url)
    #plt.show()
    #*****************************************图4：行情走势图*****************************************
    plt.figure(figsize=(8, 6))
    #股票类型，画K线图
    if testtype == '股票':
        ax1 = plt.subplot2grid((1,1), (0,0),label=u'Price Chart')
        sql_query = ("SELECT * FROM %s WHERE date>='%s' AND date<='%s' "
                        "ORDER BY date"%(table_name,start,end)
                        )
        index = 0
        result = []
        try:
            conn = sqlite3.connect(SQLITE_DATABASE_URI)
            cur = conn.cursor()
            result = cur.execute(sql_query).fetchall()
        except sqlite3.OperationalError as error:
            print('操作Sqlite3数据库出现错误，错误信息是：%s'%error)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        i = 0
        j = len(result)
        ohlc = []
        while i < j:
            date_time = datetime.datetime.strptime(result[i][1],'%Y-%m-%d')
            t = date2num(date_time)
            append_me = t, result[i][2], result[i][3], result[i][4], result[i][5], result[i][6]
            ohlc.append(append_me)
            i+=1
        candlestick_ohlc(ax1, ohlc, width=0.2, colorup='#77d879', colordown='#db3f3f')
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(45)
        ax1.xaxis.set_major_formatter(DateFormatter('%y-%m'))
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(15))
        ax1.grid(True)
        #plt.xlabel('Date')
        plt.ylabel('Price')
        str_title = u'Stock: %s'%code
        plt.title(str_title)
        plt.legend()
    #基金类型，画折线图  
    if testtype == '基金':
        sql_query = ("SELECT date,cum_netvalue FROM %s WHERE date>='%s' AND date<='%s' "
                    "ORDER BY date"%(table_name,start,end)
                    )
        try:
            conn = sqlite3.connect(SQLITE_DATABASE_URI)
            cur = conn.cursor()
            result = cur.execute(sql_query).fetchall()
        except sqlite3.OperationalError as error:
            print('操作Sqlite3数据库出现错误，错误信息是：%s'%error)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        i = 0
        j = len(result)
        x = range(len(result))
        z = []
        y = []
        t = len(x) // 10
        while i < j:
            dt = datetime.datetime.strptime(result[i][0], "%Y-%m-%d").strftime("%y-%m")
            if len(x) > 10:
                if i % t == 0:
                    z.append(dt)
                else:    
                    z.append('')
            else:
                z.append(result[i][0])
            y.append(float(result[i][1]))
            i+=1
        plt.plot(x,y,color='r',label=u'Fund: %s'%code)
        plt.xticks(x,z,rotation=45)
        #plt.xlabel(u'Date')
        plt.ylabel(u'Price')
        plt.title(u'Fund: %s'%code)
        plt.grid(False)
        str_title = u'Fund: %s'%code
    image_filename = str(dt) + '_4.png'
    image_title = u'%s：%s(%s) 在 %s 至 %s 的行情走势图'%(testtype,name,code,start,end)
    imagefiles.append({'title':image_title, 'filename':image_filename })
    imagefile_url = imagefile_dir + image_filename
    plt.savefig(imagefile_url)
    error_str = ''
    rscode = 0
    return summary, imagefiles, error_str, rscode
    
if __name__ == '__main__':
    import os
    import matplotlib.pyplot as plt
    from matplotlib.dates import AutoDateLocator, DateFormatter
    from matplotlib.font_manager import FontProperties
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
    conn = sqlite3.connect(SQLITE_DATABASE_URI)
    # cur = conn.cursor()
    start = '2000-12-01'
    end = '2003-02-2'
    fund = 5000
    period = 'monthly'
    stockcode = '000002'
    table_name = 'stock_%s'%stockcode
    btrecords, error_str, rscode = backtest(stockcode,start,end,period,fund)
    if rscode == 0:
        images, error_str, ret = backtest_chart(btrecords, stockcode)
        if ret != 0:
            print(error_str)
    else:
        print(error_str)