#!/usr/bin/env python

import os
from glob import glob
from subprocess import call

from flask_script.commands import ShowUrls, Clean
from flask_script import Command, Manager, Option, Server, Shell
from flask_migrate import Migrate, MigrateCommand
from impression import create_app
from impression.models import db, User


# default to dev config because no one should use this in
# production anyway
env = os.environ.get('FLASKAPP_ENV', 'dev')
app = create_app('impression.settings.{}Config'.format(env.capitalize()))

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

manager = Manager(app)
migrate = Migrate(app, db)


def _make_context():
    """Return context dict for a shell session so you can access app, db, and the User model by default."""
    return {'app': app, 'db': db, 'User': User}


@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code


class Lint(Command):
    """Lint and check code style with flake8 and isort."""

    def get_options(self):
        """Command line options."""
        return (
            Option('-f', '--fix-imports', action='store_true', dest='fix_imports', default=False,
                   help='Fix imports using isort, before linting'),
        )

    def run(self, fix_imports):
        """Run command."""
        skip = ['requirements']
        root_files = glob('*.py')
        root_directories = [name for name in next(os.walk('.'))[1] if not name.startswith('.')]
        files_and_directories = [arg for arg in root_files + root_directories if arg not in skip]

        def execute_tool(description, *args):
            """Execute a checking tool with its arguments."""
            command_line = list(args) + files_and_directories
            print('{}: {}'.format(description, ' '.join(command_line)))
            rv = call(command_line)
            if rv is not 0:
                exit(rv)

        if fix_imports:
            execute_tool('Fixing import order', 'isort', '-rc')
        execute_tool('Checking code style', 'flake8')


@manager.shell
def make_shell_context():
    """
    Creates a python REPL with several default imports
    in the context of the app
    """

    return dict(app=app, db=db, User=User)


@manager.command
def createdb():
    """
    Creates a database with all of the tables defined in
    the models file.
    """

    db.create_all()
    db.session.commit()


@manager.command
def dropdb():
    """
    Drops all the tables to make a fresh start.
    """

    db.drop_all()
    db.session.commit()


@manager.command
def sample_data():
    """
    Creates a set of sample data
    """
    from impression.models import Role
    user = User(username="testy", password="password")

    my_role = Role(name='admin')
    my_role.add_abilities('create_users', 'delete_users')

    user.add_roles('admin', 'superadmin')

    db.session.add(user)
    db.session.add(my_role)
    db.session.commit()

manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())
manager.add_command('lint', Lint())

if __name__ == "__main__":
    manager.run()
