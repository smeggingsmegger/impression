from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.themes2 import Themes
# from flask.ext.mail import Mail

import os

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = ''
Themes(app)

# mail = Mail(app)
# email_env = Environment(loader=PackageLoader('impression', 'templates/emails'))

db = SQLAlchemy(app)
# mail = Mail(app)

if not os.environ.get('RUNNING_ALEMBIC'):
    import views