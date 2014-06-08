import sys
import os

sys.path.append(os.path.abspath('.'))

import logging

from impression import app as application

logging.basicConfig(stream=sys.stderr)
