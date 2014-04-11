from flask import redirect, url_for, g
# from flask import request, redirect, url_for, g, session, jsonify

from impression import app
from impression.controls import render, admin_required

'''
All routes go here.
'''
@app.route('/', methods=['GET'])
def index():
    return render('index.html', user=g.user)

@admin_required
@app.route('/admin', methods=['GET'])
def admin():
    if not g.user and not g.admin:
        return redirect(url_for('login'))
    return render('admin.html', user=g.user)

@app.route('/login', methods=['GET'])
def login():
    return render('login.html', user=g.user)
