from flask_cache import Cache
try:
    from flask_debugtoolbar import DebugToolbarExtension
    debug_toolbar = DebugToolbarExtension()
except ImportError:
    debug_toolbar = None

from flask_login import LoginManager
from flask_assets import Environment
from flask_themes2 import Themes

from impression.models import User

# Setup flask cache
cache = Cache()

# Setup themes2
themes2 = Themes()

# init flask assets
assets_env = Environment()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "main_controller.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)
