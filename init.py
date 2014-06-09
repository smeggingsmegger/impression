#!/usr/bin/env python
import json
import shlex
import subprocess

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

    # Available Themes
    themes = ['Stock Bootstrap 3', 'amelia', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'lumen', 'readable', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti']
    syntax_themes = ['autumn.css', 'borland.css', 'bw.css', 'colorful.css', 'default.css', 'emacs.css', 'friendly.css', 'fruity.css', 'github.css', 'manni.css', 'monokai.css', 'murphy.css', 'native.css', 'pastie.css', 'perldoc.css', 'tango.css', 'trac.css', 'vim.css', 'vs.css', 'zenburn.css']

    # Create some system settings
    Setting(name='blog-title', vartype='str', system=True).insert()
    Setting(name='blog-copyright', vartype='str', system=True).insert()
    Setting(name='cache-timeout', vartype='int', system=True, value=0).insert()
    Setting(name='posts-per-page', vartype='int', system=True, value=4).insert()
    Setting(name='bootstrap-theme', vartype='str', system=True, value='yeti', allowed=json.dumps(themes)).insert()
    Setting(name='syntax-highlighting-theme', vartype='str', system=True, value='monokai.css', allowed=json.dumps(syntax_themes)).insert()
    Setting(name='custom-front-page', vartype='str', system=True).insert()

    safe_commit()

if __name__ == '__main__':
    main()
