# -*- coding: utf-8 -*-
import datetime
from app import app
from flask import render_template, request, flash
from flask_wtf import FlaskForm
#from flask_sqlalchemy import paginate
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from config import RECORDS_PER_PAGE
from app import db
from app.models import History_Record

class QueryForm(FlaskForm):
    stockid = StringField('股票代码', validators=[DataRequired()])
    submit = SubmitField('查询')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    queryform = QueryForm()
    if queryform.stockid.data:
        stockid = queryform.stockid.data
        records = History_Record.query.all()
        if records:
            return render_template('index.html', form=queryform, records=records)
        else:
            error_str = '无法查询到该股票'
            flash(error_str, 'warning')      
            return render_template('index.html', form=queryform)
    else:
            error_str = '没有填写股票代码'
            flash(error_str, 'warning')      
            return render_template('index.html', form=queryform)        

@app.route('/about')
def about():
    return render_template('about.html')