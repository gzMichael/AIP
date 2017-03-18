# -*- coding: utf-8 -*-
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin

#用户表
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def is_authenticated(self):
            return True

    def is_active():
        return True

    def is_anonymous(self):
            return False

    def get_id(self):
        return unicode(self.id)  

    def __repr__(self):
        return '<User %r>' % self.username

#用户回测记录表，未完成        
class UserHistory(db.Model):
    __tablename__ = 'user_history'
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    stockid = db.Column(db.String(64))
    date = db.Column(db.String(64))
    
    def __repr__(self):
        return '%s(%r %r %r)' %(self.__class__.__name__, self.userid, self.date, self.stockid)

#股票历史行情
class StockHistory(db.Model):
    __tablename__ = 'stock_history'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(40))
    open = db.Column(db.Float)
    close = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    volume = db.Column(db.Float)
    code = db.Column(db.String(20))
    
    def __init__(self):
        pass

    def __repr__(self):
        return '%s(%r %r %r)' %(self.__class__.__name__, self.code, self.date, self.close)
