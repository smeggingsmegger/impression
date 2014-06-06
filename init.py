#!/usr/bin/env python
import json
import shlex
import subprocess

from werkzeug.security import generate_password_hash

# from impression import app
from impression.mixin import safe_commit
from impression.models import *

def main():
    """@todo: Docstring for main.
    :returns: @todo

    """
    print("Initializing DB...")
    db.drop_all(bind=[None])
    db.create_all(bind=[None])
    print("Getting latest alembic revision since we are generating this DB")
    args = shlex.split("alembic history")
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, error = p.communicate()
    data = output.split('\n')
    latest_alembic = None
    for row in data:
        if "(head)" in row:
            cols = row.split(" ")
            latest_alembic = cols[2].strip()

    if latest_alembic:
        print("Stamping with latest Alembic revision: %s" % latest_alembic)
        args = shlex.split("alembic stamp %s" % latest_alembic)
        subprocess.Popen(args, stdout=subprocess.PIPE)

    hashed_password = generate_password_hash('testy21')

    # Create a user to update and delete later.
    User(name="Test User", email='test@test.com', admin=True, openid='', password=hashed_password).insert()

    # Available Themes
    themes = ['Stock Bootstrap 3', 'amelia', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'lumen', 'readable', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti']
    syntax_themes = ['autumn.css', 'borland.css', 'bw.css', 'colorful.css', 'default.css', 'emacs.css', 'friendly.css', 'fruity.css', 'github.css', 'manni.css', 'monokai.css', 'murphy.css', 'native.css', 'pastie.css', 'perldoc.css', 'tango.css', 'trac.css', 'vim.css', 'vs.css', 'zenburn.css']

    # Create some system settings
    Setting(name='blog-title', type='str', system=True).insert()
    Setting(name='blog-copyright', type='str', system=True).insert()
    Setting(name='cache-timeout', type='int', system=True, value=0).insert()
    Setting(name='bootstrap-theme', type='str', system=True, value='yeti', allowed=json.dumps(themes)).insert()
    Setting(name='syntax-highlighting-theme', type='str', system=True, value='monokai.css', allowed=json.dumps(syntax_themes)).insert()

    safe_commit()

if __name__ == '__main__':
    main()
