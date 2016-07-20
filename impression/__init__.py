from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_themes2 import Themes
from flask_cache import Cache
# from flask_mail import Mail

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

# Remove cache limit from Jinja
app.jinja_env.cache = {}

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.abspath(APP_ROOT + '/cache/')
cache_type = 'null'

cache = Cache(app, config={'CACHE_TYPE': cache_type})
# cache = Cache(app, config={'CACHE_TYPE': cache_type, 'CACHE_DIR': cache_dir})

Themes(app)

# mail = Mail(app)
# email_env = Environment(loader=PackageLoader('impression', 'templates/emails'))

db = SQLAlchemy(app)
# mail = Mail(app)

if not os.environ.get('RUNNING_ALEMBIC'):
    import impression.views
