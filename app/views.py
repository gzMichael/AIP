# -*- coding: utf-8 -*-
import datetime
from app import app, db, lm
from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
#from flask_sqlalchemy import paginate
from wtforms import StringField, SubmitField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from config import RECORDS_PER_PAGE
from app.models import User, StockHistory, UserHistory

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
    
class QueryForm(FlaskForm):
    '''回测表格'''
    stockid = StringField('股票代码', validators=[DataRequired()])
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
@login_required
def index():
    queryform = QueryForm()
    if request.method == 'POST':
        if queryform.stockid.data:
            stockid = queryform.stockid.data
            records = StockHistory.query.all()
            if records:
                return render_template('index.html', form=queryform, records=records, user=g.user)
            else:
                error_str = '无法查询到该股票'
                flash(error_str, 'warning')      
                return render_template('index.html', form=queryform, user=g.user)
        else:
                error_str = '请填写股票代码'
                flash(error_str, 'warning')      
                return render_template('index.html', form=queryform, user=g.user)

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