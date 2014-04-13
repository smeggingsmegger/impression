from flask import redirect, request, url_for, g, jsonify
# from flask import request, redirect, url_for, g, session, jsonify

from impression import app
from impression.controls import render, admin_required, key_or_admin_required, get_payload
from impression.mixin import safe_commit
from impression.models import User
from impression.utils import success, failure

from werkzeug.security import generate_password_hash

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
        hashed_password = generate_password_hash(payload.get('password'))
        user = User()
        user.email = payload.get('email')
        user.name = payload.get('name')
        user.password = hashed_password
        user.insert()
        safe_commit()
        return_value['user_id'] = user.id
    else:
        return_value = failure('That user exists already.')

    return jsonify(return_value)

@app.route('/user_retrieve', methods=['POST'])
@key_or_admin_required
def retrieve_user():
    # TODO: Remove password, openid keys when sending it back.
    return_value = success('The user was retrieved.')
    payload = get_payload(request)
    user = User.get(payload.get('id'))

    if not user:
        return_value = failure('That user does not exist.')
    else:
        return_value['user'] = user.to_dict(camel_case=True)

    return jsonify(return_value)

@app.route('/user_update', methods=['POST'])
@key_or_admin_required
def update_user():
    return_value = success('The user was updated.')
    payload = get_payload(request)
    user = User.get(payload.get('id'))

    if not user:
        return_value = failure('That user does not exist.')
    else:
        if payload.get('password'):
            hashed_password = generate_password_hash(payload.get('password'))
        if payload.get('email'):
            user.email = payload.get('email')
        if payload.get('name'):
            user.name = payload.get('name')

        user.password = hashed_password
        safe_commit()
        return_value['user'] = user.to_dict(camel_case=True)

    return jsonify(return_value)

@app.route('/user_delete', methods=['POST'])
@key_or_admin_required
def delete_user():
    return_value = success('The user was deleted.')
    payload = get_payload(request)

    if not g.user or g.user.id != payload.get('id'):
        user = User.filter(User.id == payload.get('id')).first()
        if user:
            user.delete()
            safe_commit()
        else:
            return_value = failure('That user does not exist.')
    else:
        return_value = failure('You cannot delete the current user.')

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
