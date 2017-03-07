import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'AIP_secret_key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'stock.sqlite')
SQLALCHEMY_TRACK_MODIFICATIONS = True
RECORDS_PER_PAGE = 20