# -*- coding: utf-8 -*-
import os
import datetime
import sqlite3
from app import app, db, lm
from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User, StockHistory, UserHistory
from app.backtest import backtest, backtest_chart

class LoginForm(FlaskForm):
    '''用户登陆表格'''
    username = StringField('用户名：', validators=[DataRequired()])
    password = PasswordField('密码：', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登入')

class RegisterForm(FlaskForm):
    '''用户注册表格'''
    username = StringField('用户名：', validators=[DataRequired()])
    password = PasswordField('新密码：', validators=[DataRequired(), EqualTo('password2', message='两次密码输入必须一致')])
    password2 = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')

def check_date_input(form, field):
    if field.data:
        try:
            dt = datetime.datetime.strptime(field.data, "%Y-%m-%d")
        except:
            raise ValidationError('正确的日期格式为：YYYY-mm-dd')

def check_fund_input(self, field):
        if field.data:
            try:
                f = float(field.data)
            except:    
                raise ValidationError('请输入正确的定投数额')
            else:
                if f <= 0:
                    raise ValidationError('请输入大于零的定投数额')
            
class QueryForm(FlaskForm):
    '''回测表格'''
    stockid = StringField('股票代码(如:600000)', validators=[DataRequired()])
    selection = SelectField('代码类型：基金/股票', choices=[(0,'股票'),(1,'基金')])
    start = StringField('开始日期(YYYY-mm-dd)', validators=[DataRequired(), check_date_input])
    end = StringField('结束日期(YYYY-mm-dd)', validators=[DataRequired(), check_date_input])
    period = SelectField('定投间隔', coerce=str, choices=[('monthly','每月'),('yearly','每年')])
    fund = StringField('定投金额(如:1000)', validators=[DataRequired(), check_fund_input])
    submit = SubmitField('测试')
    
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

# @app.before_request
# def before_request():
    # g.user = current_user

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误，请重新输入。', 'danger')
    return render_template('login.html', form=form)
 
 
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    queryform = QueryForm()
    if request.method == 'POST':
        if queryform.validate():
            stockid = queryform.stockid.data
            table_name = 'stock_%s'%stockid
            start = queryform.start.data
            end = queryform.end.data
            period = queryform.period.data
            selection = queryform.selection.data
            if selection == 0:
                selection_str = '股票'
            else:
                selection_str = '基金'
            fund = float(queryform.fund.data)
            print('stockid=%s, start=%s, end=%s, period=%s, fund=%s'%(stockid,start,end,period,fund))
            basedir = os.path.abspath(os.path.dirname(__file__))
            SQLITE_DATABASE_URI = os.path.join(basedir, '../stock.sqlite')
            sql_query = "SELECT code FROM stock_basics WHERE code='%s'"%stockid
            print(sql_query)
            try:
                conn = sqlite3.connect(SQLITE_DATABASE_URI)
                try:
                    rs = conn.execute(sql_query).fetchall()
                finally:
                    if conn:
                        conn.close()
                if len(rs) > 0:
                    btrecords = []
                    btrecords, error_str, rscode = backtest(selection, stockid, start, end, period, fund)
                    print('len(btrecords)=%s'%len(btrecords))
                    if rscode == 0:
                        images, error_str, ret = backtest_chart(btrecords, stockid)
                        if ret == 0:
                            print('images=%s'%images)
                            return render_template('showresult.html', form=queryform, images=images)
                        else:
                            flash(error_str, 'warning')
                    else:
                        flash(error_str, 'warning')
                else:
                    error_str = '无法查询到该%s'%selection_str
                    flash(error_str, 'warning')
            finally:
                if conn:
                    conn.close()
    return render_template('index.html', form=queryform)

@app.route('/history')
def history():
    return render_template('history.html')
    
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None:
            flash('用户已存在，请重新选择用户名。', 'danger')
            return render_template('register.html', form=form)
        else:    
            new_user = User(form.username.data, form.password.data)
            new_user.authenticated = True
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html', form=form)