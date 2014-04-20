import os

# Database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath("impression/impression.db")

# Your mail server configuration here.
MAIL_SERVER = 'smtp.somehost.net'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = 'admin@somehost.com'

# Replace this with something real.
SERVER_PATH = 'srv/www'
DEFAULT_THEME = 'impression'

# File upload settings
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tiff'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
