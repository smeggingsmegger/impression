import sys
from functools import wraps

# from flask import flash, abort, Blueprint
from flask import request, redirect, url_for, g, session, jsonify, render_template

from impression import app
from impression.models import User, Setting, ApiKey

# theme = Blueprint('theme', __name__, static_folder='themes/{}/static'.format('impression'))
# app.register_blueprint(theme)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', user=g.user)

@app.route('/admin', methods=['GET'])
def admin():
    if not g.user and not g.admin:
        return redirect(url_for('login'))
    return render_template('admin.html', user=g.user)

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
    g.theme = "impression"

    if 'admin' in session and session['admin']:
        g.admin = True

    if 'userid' in session:
        g.user = User.get(session['userid'])
