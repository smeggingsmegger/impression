import os
import tempfile

db_file = tempfile.NamedTemporaryFile()

# APP_ROOT = os.path.dirname(os.path.abspath(__file__))  # Don't touch this.


class Config(object):
    SECRET_KEY = 'REPLACE THIS KEY ASAP'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_NO_NULL_WARNING = True
    DEBUG = True
    # UPLOAD_FOLDER = os.path.abspath(APP_ROOT + '/../uploads/')
    # ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tiff'])
    # MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class ProdConfig(Config):
    ENV = 'prod'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../impression/impression.db'

    CACHE_TYPE = 'simple'
    DEBUG = False


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///../impression/impression.db'

    CACHE_TYPE = 'null'
    ASSETS_DEBUG = True


class TestConfig(Config):
    ENV = 'test'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_file.name
    SQLALCHEMY_ECHO = True

    CACHE_TYPE = 'null'
    WTF_CSRF_ENABLED = False
