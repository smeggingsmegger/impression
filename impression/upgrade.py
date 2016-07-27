from impression.mixin import safe_commit
from impression.models import Setting
from impression.utils import filter_results

try:
    import simplejson as json
except ImportError:
    import json


# Available Themes
THEMES = ['Stock Bootstrap 3', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'journal',
          'lumen', 'readable', 'sandstone', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti']

SYNTAX_THEMES = ['autumn.css', 'borland.css', 'bw.css', 'colorful.css', 'default.css', 'emacs.css',
                 'friendly.css', 'fruity.css', 'github.css', 'manni.css', 'monokai.css', 'murphy.css',
                 'native.css', 'pastie.css', 'perldoc.css', 'tango.css', 'trac.css', 'vim.css', 'vs.css',
                 'zenburn.css']


def upgrade_settings():
    settings = Setting.all()
    print(settings)

    bootstrap_theme = filter_results(settings, 'name', 'bootstrap-theme')[0]
    if json.loads(bootstrap_theme.allowed) != THEMES:
        print("Upgrading allowed Bootstrap themes.")
        bootstrap_theme.allowed = json.dumps(THEMES)
        if bootstrap_theme.value not in THEMES:
            print("Old theme not allowed. Setting random one.")
            bootstrap_theme.value = THEMES[0]
        bootstrap_theme.insert()

    syntax_theme = filter_results(settings, 'name', 'syntax-highlighting-theme')[0]
    if json.loads(syntax_theme.allowed) != SYNTAX_THEMES:
        print("Upgrading allowed syntax highlighting themes.")
        syntax_theme.allowed = json.dumps(SYNTAX_THEMES)
        if syntax_theme.value not in SYNTAX_THEMES:
            print("old syntax highlighting theme not allowed. Setting random one.")
            syntax_theme.value = SYNTAX_THEMES[0]
        syntax_theme.insert()

    safe_commit()


def upgrade():
    upgrade_settings()
