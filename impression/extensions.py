from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
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

debug_toolbar = DebugToolbarExtension()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "main_controller.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)
