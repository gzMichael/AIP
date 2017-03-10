# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import os

basedir = os.path.abspath(os.path.dirname(__file__))
stockstr = '600848'
df = ts.get_k_data(stockstr, start='1990-03-05', end='2017-03-08')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '../stock.sqlite')
print(basedir)
print(SQLALCHEMY_DATABASE_URI)
engine = create_engine(SQLALCHEMY_DATABASE_URI)
df.to_sql(stockstr,engine,if_exists='append')
