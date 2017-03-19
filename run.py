# -*- coding: utf-8 -*-  

from app import app
from flask_bootstrap import Bootstrap

if __name__ == '__main__':
    app.debug = True
    bootstrap = Bootstrap(app)
    app.run(host='0.0.0.0', port=80)