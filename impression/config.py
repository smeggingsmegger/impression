import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))  # Don't touch this.

SERVER_PATH = APP_ROOT

#############################################
#   Everything below here is configurable   #
#############################################

# Database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(APP_ROOT + "/impression.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
CACHE_NO_NULL_WARNING = True
CACHE_TYPE = 'null'

# Your mail server configuration here.
MAIL_SERVER = 'smtp.somehost.net'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = 'admin@somehost.com'

# Theme settings
DEFAULT_THEME = 'impression'

# File upload settings
UPLOAD_FOLDER = os.path.abspath(APP_ROOT + '/../uploads/')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tiff'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
