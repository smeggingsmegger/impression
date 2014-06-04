# import sys
import re
from functools import wraps

from impression import app
from impression.models import Setting, ApiKey, User, Content

from flask import request, redirect, url_for, g, jsonify, session
from flask.ext.themes2 import get_theme, render_theme_template

from itsdangerous import TimestampSigner, SignatureExpired

'''
Misc functions that do things like get the current theme and render templates.
'''
def get_setting(name, default):
    setting = Setting.filter(Setting.name == name).first()
    if setting:
        return setting.val
    else:
        return default

def make_slug(title, delimiter='-'):
    slug = delimiter.join([w for w in re.sub('[^\w ]', '', title.replace('-', ' ')).lower().split(' ') if w])
    count = Content.filter(Content.slug == slug).count()
    slug = slug if count == 0 else "{0}{1}{2}".format(slug, delimiter, count)
    return slug

def is_slug(slug):
    return bool(re.search('^[a-z]+-?', slug))

def get_current_theme(app, g):
    if g.theme is not None:
        ident = g.theme
    else:
        ident = app.config.get('DEFAULT_THEME')
    return get_theme(ident)

def get_settings():
    '''
    Gets all the settings for the app.
    '''
    settings = {}
    all_settings = Setting.all()
    for setting in all_settings:
        settings[setting.name.strip()] = setting.val

    return settings

def get_api_key(request):
    try:
        api_key_name = request.POST.get('api_key', '')
    except AttributeError:
        api_key_name = request.form.get('api_key', '')

    # There is probably a better way to do this.
    api_keys = ApiKey.all()
    api_key = None
    for ak in api_keys:
        if api_key_name.startswith(ak.name):
            try:
                s = TimestampSigner(ak.key)
                s.unsign(api_key_name, max_age=120)
                api_key = ak
            except SignatureExpired:
                pass

    return api_key

def get_payload(request):
    try:
        payload = request.POST
    except AttributeError:
        payload = request.form

    return payload

'''
All decorators below. These handle things like authentication and more.
'''
def key_or_admin_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key(request)
        if not api_key and not g.user:
            if not api_key:
                # print >> sys.stderr, "No valid API Key found."
                return(jsonify({'success': False, 'messages': ['No valid API Key found.']}))
            if not g.user.admin:
                # print >> sys.stderr, "No admin user found."
                return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

def key_or_login_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key(request)
        if not api_key or not g.user:
            if not api_key:
                # print >> sys.stderr, "No valid API Key found."
                return(jsonify({'error': 'No valid API Key found.'}))
            if not g.user:
                # print "No user found."
                return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

def key_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key(request)
        if not api_key:
            # print >> sys.stderr, "No valid API Key found."
            return(jsonify({'error': 'No valid API Key found.'}))
        return fnctn(*args, **kwargs)
    return decorated_function

def login_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        if not g.user:
            # print "No user found."
            return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

def admin_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        if g.user:
            if not g.user.admin and not g.user.admin:
                return redirect(url_for('login', next=request.url))
        else:
            return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

'''
This is a special render that allows us to use themes.
'''
def render(template, **context):
    return render_theme_template(get_current_theme(app, g), template, **context)

'''
Before we process any request, let's do some things.
'''
@app.before_request
def before_request():
    g.user = None
    g.theme = 'impression'

    if 'userid' in session:
        g.user = User.get(session['userid'])
