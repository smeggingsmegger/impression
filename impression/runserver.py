#!/usr/bin/env python
import os
from impression import create_app


def main():
    # Get config and create app pattern.
    env = os.environ.get('IMPRESSION_ENV', 'prod')
    host = os.environ.get('IMPRESSION_HOST', '0.0.0.0')
    app = create_app('impression.settings.{}Config'.format(env.capitalize()))
    app.run(debug=app.config['DEBUG'], host=host)

# @app.before_request
if __name__ == "__main__":
    main()
