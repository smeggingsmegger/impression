#!/usr/bin/env python
try:
    import click
except ImportError:
    import sys
    print("This utility requires the library: click\n\nTo install, use pip or some other similar tool. \"pip install click\"")
    sys.exit()

from werkzeug.security import generate_password_hash

from impression.mixin import safe_commit
from impression.models import User

@click.command()
@click.option('--name', prompt='Your Name', help='Your actual name. Example: John Smith')
@click.option('--email', prompt='Your Email Address', help='Your email address. Example: johnsmith@some-domain-here.com')
@click.option('--password', prompt='Your Password', help='Your Password. Example: th1s1sn0ts3cur3')
def main(name, email, password):
    hashed_password = generate_password_hash(password)
    # Create a user to update and delete later.
    User(name=name, email=email, admin=True, openid='', password=hashed_password).insert()
    safe_commit()

if __name__ == '__main__':
    main()
