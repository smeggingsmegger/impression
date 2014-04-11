from flask import redirect, request, url_for, g, jsonify
# from flask import request, redirect, url_for, g, session, jsonify

from impression import app
from impression.controls import render, admin_required, key_or_admin_required, get_payload
from impression.mixin import safe_commit
from impression.models import User
from impression.utils import success, failure

'''
All routes go here.
'''
@app.route('/', methods=['GET'])
def index():
    return render('index.html', user=g.user)

@app.route('/user_create', methods=['POST'])
@key_or_admin_required
def create_user():
    return_value = success('The user was created.')
    payload = get_payload(request)
    existing_user = User.filter(User.email == payload.get('email')).count()

    if not existing_user:
        user = User()
        user.email = payload.get('email')
        user.name = payload.get('name')
        user.password = payload.get('password')
        user.insert()
        safe_commit()
    else:
        return_value = failure('That user exists already.')

    return jsonify(return_value)

@admin_required
@app.route('/admin', methods=['GET'])
def admin():
    if not g.user and not g.admin:
        return redirect(url_for('login'))
    return render('admin.html', user=g.user)

@app.route('/login', methods=['GET'])
def login():
    return render('login.html', user=g.user)
