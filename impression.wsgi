import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

import logging

from impression import create_app
env = os.environ.get('IMPRESSION_ENV', 'prod')
host = os.environ.get('IMPRESSION_HOST', '0.0.0.0')
application = create_app('impression.settings.{}Config'.format(env.capitalize()))

logging.basicConfig(stream=sys.stderr)
