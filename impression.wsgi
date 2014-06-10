import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

import logging

from impression import app as application

logging.basicConfig(stream=sys.stderr)
