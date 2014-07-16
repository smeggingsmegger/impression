import os
# Don't touch this.
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

SERVER_PATH = APP_ROOT

#############################################
#   Everything below here is configurable   #
#############################################

# Database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(APP_ROOT + "/impression.db")

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
