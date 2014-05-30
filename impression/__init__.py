from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.themes2 import Themes
# from flask.ext.mail import Mail

import os

# Yay! I love coding Python X :(
try:
    unicode = unicode
except NameError:
    # unicode is undefined: We are running Python 3
    unicode = str
    basestring = (str, bytes)
else:
    # unicode is defined: We are running Python 2
    bytes = str

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = os.urandom(24)

Themes(app)

# mail = Mail(app)
# email_env = Environment(loader=PackageLoader('impression', 'templates/emails'))

db = SQLAlchemy(app)
# mail = Mail(app)

if not os.environ.get('RUNNING_ALEMBIC'):
    import views
