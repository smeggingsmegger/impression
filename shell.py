#!/usr/bin/env python
from impression import *
from impression.models import *
from impression.mixin import *
from flask import *

def main():
    """@todo: Docstring for main.
    :returns: @todo

    """
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
