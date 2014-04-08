import sys
from impression.config import SERVER_PATH

sys.path.insert(0, SERVER_PATH)
import logging

from impression import app as application

logging.basicConfig(stream=sys.stderr)
