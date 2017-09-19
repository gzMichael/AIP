# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object('config')
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager()
lm.setup_app(app)
lm.login_view = 'login'

from app import views
from app import models
from app.models import StockHistory

db.create_all()
#engine = create_engine(SQLALCHEMY_DATABASE_URI)

#df = ts.get_k_data('600320',start='1900-01-01',end='2017-12-31')
#存入数据库
#df.to_sql('historyrecord',engine,if_exists='append')

