#!/usr/bin/env python
import shutil
import os
from impression import create_app
from impression.models import Content  # , Setting
from impression.controls import render, get_menu_items, get_current_theme
# from impression.mixin import db, safe_commit

# Get config and create app pattern.
env = os.environ.get('IMPRESSION_ENV', 'prod')
host = os.environ.get('IMPRESSION_HOST', '0.0.0.0')
app = create_app('impression.settings.{}Config'.format(env.capitalize()))

FROZEN_DIR = 'frozen/'


def get_theme_dirs():
    theme_dirs = []
    for file in os.listdir('impression/themes/'):
        if file != 'admin':
            path = os.path.abspath(os.path.join('impression/themes/', file))
            theme_dirs.append((file, path))
    return theme_dirs


def theme_static(the_file, **kwargs):
    theme = get_current_theme()
    return '{}/static/{}'.format(theme.identifier, the_file)


def main():
    """@todo: Docstring for main.
    :returns: @todo

    """
    # Clear the frozen directory
    for file in os.listdir(FROZEN_DIR):
        if file != '.empty':
            path = os.path.abspath(os.path.join(FROZEN_DIR, file))
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    # Copy themes
    theme_dirs = get_theme_dirs()
    for theme_dir in theme_dirs:
        dest = os.path.join(FROZEN_DIR, theme_dir[0])
        shutil.copytree(theme_dir[1], dest)

    # Render all the templates
    with app.app_context():
        theme = get_current_theme()
        app.jinja_env.globals['theme_static'] = theme_static
        contents = Content.filter(Content.published == True).all()
        for content in contents:
            template = content.template
            f_template = 'freeze-{}'.format(content.template)
            freeze_template = os.path.join('impression/themes/',
                                           theme.identifier,
                                           'templates/',
                                           f_template)
            if (os.path.isfile(os.path.abspath(freeze_template))):
                template = f_template

            html = render(template, content=content, menu_items=get_menu_items(), freeze=True)
            with open('frozen/{}.html'.format(content.slug), 'w') as f:
                f.write(html)


if __name__ == '__main__':
    main()
