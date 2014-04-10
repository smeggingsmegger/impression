import sys
from functools import wraps

from flask import request, redirect, url_for, g, session, jsonify
from flask.ext.themes2 import get_theme, render_theme_template

from impression import app
from impression.models import User, Setting, ApiKey

def get_current_theme():
    if g.theme is not None:
        ident = g.theme
    else:
        ident = app.config.get('DEFAULT_THEME')
    return get_theme(ident)

def render(template, **context):
    return render_theme_template(get_current_theme(), template, **context)

@app.route('/', methods=['GET'])
def index():
    return render('index.html', user=g.user)

@app.route('/admin', methods=['GET'])
def admin():
    if not g.user and not g.admin:
        return redirect(url_for('login'))
    return render('admin.html', user=g.user)

@app.route('/login', methods=['GET'])
def login():
    return render('login.html', user=g.user)

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
        api_key_id = request.POST['api_key']
    except AttributeError:
        api_key_id = request.form.get('api_key')

    api_key = ApiKey.filter_by(key=api_key_id).first()
    return api_key

def key_or_login_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key(request)
        if not api_key or not g.user:
            if not api_key:
                print >> sys.stderr, "No valid API Key found."
                return(jsonify({'error': 'No valid API Key found.'}))
            if not g.user:
                print "No user found."
                return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

def key_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key(request)
        if not api_key:
            print >> sys.stderr, "No valid API Key found."
            return(jsonify({'error': 'No valid API Key found.'}))
        return fnctn(*args, **kwargs)
    return decorated_function

def login_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        if not g.user:
            print "No user found."
            return redirect(url_for('login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

def admin_required(fnctn):
    @wraps(fnctn)
    def decorated_function(*args, **kwargs):
        if not g.user.admin and not g.admin:
            return redirect(url_for('admin_login', next=request.url))
        return fnctn(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    g.user = None
    g.admin = False
    g.theme = 'impression'

    if 'admin' in session and session['admin']:
        g.admin = True

    if 'userid' in session:
        g.user = User.get(session['userid'])
