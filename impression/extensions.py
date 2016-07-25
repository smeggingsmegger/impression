from impression.models import User

try:
    from flask_cache import Cache
    # Setup flask cache
    cache = Cache()
except ImportError:
    cache = None

try:
    from flask_debugtoolbar import DebugToolbarExtension
    debug_toolbar = DebugToolbarExtension()
except ImportError:
    debug_toolbar = None

try:
    from flask_assets import Environment
    # init flask assets
    assets_env = Environment()
except ImportError:
    assets_env = None

from flask_themes2 import Themes
# Setup themes2
themes2 = Themes()

from flask_login import LoginManager
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "main_controller.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)
