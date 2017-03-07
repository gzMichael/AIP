# -*- coding: utf-8 -*-
from app import db
        
class History_Record(db.Model):
    __tablename__ = 'historyrecord'
    rowid = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer)
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
