#!/usr/bin/env python
import os
from impression import create_app

# Get config and create app pattern.
env = os.environ.get('IMPRESSION_ENV', 'prod')
host = os.environ.get('IMPRESSION_HOST', '0.0.0.0')
app = create_app('impression.settings.{}Config'.format(env.capitalize()))

from impression.models import User, Setting, Role, Ability
from impression.mixin import db, safe_commit
# from flask import *

def main():
    """@todo: Docstring for main.
    :returns: @todo

    """
    with app.app_context():
        try:
            from IPython import embed
            embed()
        except ImportError:
            import os
            import readline
            from pprint import pprint
            os.environ['PYTHONINSPECT'] = 'True'

if __name__ == '__main__':
    main()
