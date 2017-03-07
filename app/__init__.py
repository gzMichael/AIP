# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI
import tushare as ts

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from app import views
from app import models
from app.models import History_Record

#db.create_all()
#engine = create_engine(SQLALCHEMY_DATABASE_URI)

#df = ts.get_k_data('600320',start='1900-01-01',end='2017-12-31')
#存入数据库
#df.to_sql('historyrecord',engine,if_exists='append')

