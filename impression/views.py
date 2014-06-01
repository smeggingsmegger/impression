import os
import json
from dateutil import parser
from datetime import datetime

from flask import redirect, request, url_for, g, jsonify, send_from_directory, flash, session
# from flask import request, redirect, url_for, g, session, jsonify

from impression import app
from impression.controls import render, admin_required, key_or_admin_required, get_payload, make_slug
from impression.mixin import paginate, results_to_dict, safe_commit
from impression.models import User, Content, File, Tag
from impression.utils import success, failure

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

'''
All routes go here.
'''
@app.route('/', methods=['GET'])
def index():
    return render('index.html', user=g.user)

'''
IMAGE ROUTES
'''
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_ajax', methods=['POST'])
def upload_ajax():
    return_value = success('The file was uploaded.')
    payload = get_payload(request)
    ufile = request.files['file']
    file_id = upload_file(payload, ufile)
    return_value['id'] = file_id
    return jsonify(return_value)

@app.route('/upload', methods=['POST'])
def upload():
    payload = get_payload(request)
    ufile = request.files['file']
    file_id = upload_file(payload, ufile)
    if file_id:
        flash("File uploaded!")
    else:
        flash("There was a problem uploading that file.")
    return redirect("/admin/files/add")

def upload_file(payload, ufile):
    if ufile and allowed_file(ufile.filename):
        filename = secure_filename(ufile.filename)
        path = os.path.join(".", app.config['UPLOAD_FOLDER'], filename)
        if not os.path.isfile(path):
            ufile.save(path)
            try:
                # Create thumbnail
                from PIL import Image
                size = 128, 128
                im = Image.open(path)
                width, height = im.size
                im.thumbnail(size, Image.ANTIALIAS)
                file, ext = os.path.splitext(path)
                ext = ext.lower()
                etype = ext.replace(".", "")
                if etype == 'jpg':
                    etype = 'jpeg'
                im.save(file + "_thumbnail" + ext, etype)
            except (ImportError, IOError):
                width = 0
                height = 0

            afile = File(name=filename, user_id=payload.get('user_id'), path=path, size=os.path.getsize(path), width=width, height=height, mimetype=ufile.mimetype)
            afile.insert()
            safe_commit()
            return afile.id
    return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    path = os.path.abspath("./" + app.config['UPLOAD_FOLDER'])
    return send_from_directory(path, filename)

@app.route('/get_tags', methods=['GET'])
def get_tags():
    tags = [t.name for t in Tag.all()]
    return json.dumps(tags)

'''
CONTENT ROUTES
'''
@app.route('/page/<string:content_id>', methods=['GET'])
def render_page(content_id):
    content = Content.get(content_id)
    if not content:
        content = Content.filter(Content.slug == content_id).first()
    return render('page.html', user=g.user, content=content)

@app.route('/post/<string:content_id>', methods=['GET'])
def render_post(content_id):
    content = Content.get(content_id)
    if not content:
        content = Content.filter(Content.slug == content_id).first()
    return render('post.html', user=g.user, content=content)

@app.route('/content_create', methods=['POST'])
@key_or_admin_required
def create_content():
    return_value = success('The content was created.')
    payload = get_payload(request)

    editing = False
    if payload.get('id'):
        content = Content.get(payload.get('id'))
        editing = True
        return_value = success('The content was updated.')
    else:
        content = Content()

    content.type = payload.get('type').lower()
    content.title = payload.get('title')
    content.body = payload.get('body')
    content.user_id = payload.get('user_id')
    tags = [t.strip() for t in payload.get('tags', '').split(',') if t.strip()]
    for tag in tags:
        count = Tag.filter(Tag.name == tag).count()
        if not count:
            new_tag = Tag(name=tag)
            new_tag.insert()

    content.tags = ",".join(tags)
    content.parser = payload.get('parser', 'markdown')
    content.published = bool(payload.get('published', False))

    if not editing:
        content.slug = make_slug(content.title)
    else:
        created_on = payload.get('created_on')
        if created_on:
            content.created_on = parser.parse(created_on)

    valid = content.validate()
    if valid['success'] or editing:
        content.insert()
        safe_commit()
        return_value['id'] = content.id
    else:
        return_value = valid

    return jsonify(return_value)

@app.route('/content_retrieve', methods=['POST'])
def retrieve_content():
    return_value = success('The content was retrieved.')
    return_value['contents'] = []

    payload = get_payload(request)

    content_id = payload.get('id')
    if content_id:
        content = Content.get(content_id)
        if content:
            return_value['contents'] = [content.to_dict(camel_case=True)]
        else:
            return_value['success'] = False
            return_value['messages'] = ['No content found with that ID.']
    else:
        # No ID passed... we should return more than one result.
        current_page = payload.get('current_page', 1)
        page_size = payload.get('page_size', 5)
        content_type = payload.get('content_type', 'post')
        published = payload.get('published', True)
        contents = Content.filter(Content.type == content_type)\
                          .filter(Content.published == published)\
                          .order_by(Content.published_on.desc())

        contents, maxpages = paginate(contents, current_page, page_size)
        if contents:
            return_value['contents'] = results_to_dict(contents, camel_case=True)

    return jsonify(return_value)

'''
USER ROUTES
'''
@app.route('/user_create', methods=['POST'])
@key_or_admin_required
def create_user():
    return_value = success('The user was created.')
    payload = get_payload(request)

    hashed_password = generate_password_hash(payload.get('password'))

    user = User()
    user.email = payload.get('email')
    user.name = payload.get('name')
    user.password = hashed_password
    valid = user.validate()

    if valid['success']:
        user.insert()
        safe_commit()
        return_value['id'] = user.id
    else:
        del(user)
        return_value = valid

    return jsonify(return_value)

@app.route('/user_retrieve', methods=['POST'])
@key_or_admin_required
def retrieve_user():
    return_value = success('The user was retrieved.')
    payload = get_payload(request)
    user = User.get(payload.get('id'))

    if not user:
        return_value = failure('That user does not exist.')
    else:
        return_value['user'] = user.to_dict(camel_case=True)
        return_value['user'].pop('password')
        return_value['user'].pop('openid')

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

'''
ADMIN ROUTES
'''
@app.route('/admin/files', methods=['GET'])
@admin_required
def admin_files_list():
    files = File.all()
    return render('admin_files_list.html', files=files)

@app.route('/admin/files/add', methods=['GET'])
@admin_required
def admin_files_add():
    return render('admin_file.html')

@app.route('/admin/pages/add', methods=['GET'])
@admin_required
def admin_pages_add():
    content = Content()
    content.created_on = datetime.now()
    content.body = ''
    content.title = ''
    content.tags = ''
    content.parser = 'markdown'
    return render('admin_content.html', user=g.user, content_type="Page", action="Add", content=content)

@app.route('/admin/pages/edit/<string:content_id>', methods=['GET'])
@admin_required
def admin_pages_edit(content_id):
    content = Content.get(content_id)
    return render('admin_content.html', user=g.user, content_type=content.type, action="Edit", content=content)

@app.route('/admin/pages', methods=['GET'])
@admin_required
def admin_pages_list():
    contents = Content.filter(Content.type == 'page').all()
    return render('admin_content_list.html', contents=contents, content_type="Pages")

@app.route('/admin/posts/add', methods=['GET'])
@admin_required
def admin_posts_add():
    content = Content()
    content.created_on = datetime.now()
    content.body = ''
    content.title = ''
    content.tags = ''
    content.parser = 'markdown'
    return render('admin_content.html', user=g.user, content_type="Post", action="Add", content=content)

@app.route('/admin/posts/edit/<string:content_id>', methods=['GET'])
@admin_required
def admin_posts_edit(content_id):
    content = Content.get(content_id)
    return render('admin_content.html', user=g.user, content_type=content.type, action="Edit", content=content)

@app.route('/admin/posts', methods=['GET'])
@admin_required
def admin_posts_list():
    contents = Content.filter(Content.type == 'post').all()
    return render('admin_content_list.html', contents=contents, content_type="Posts")

@app.route('/admin', methods=['GET'])
@app.route('/admin/', methods=['GET'])
@admin_required
def admin():
    return render('admin_index.html', user=g.user)

@app.route('/logout', methods=['GET'])
def logout():
    session['userid'] = None
    return render('login.html')

@app.route('/login', methods=['GET'])
def login():
    if g.user and g.user.admin:
        return redirect(url_for('admin'))
    return render('login.html')

@app.route('/post_login', methods=['POST'])
def post_login():
    payload = get_payload(request)
    user = User.filter(User.email == payload.get('email')).first()
    if user:
        if check_password_hash(user.password, payload['password']):
            session['userid'] = user.id
            next_url = request.args.get('next', '')
            if next_url:
                return redirect(next_url)
            else:
                return redirect(url_for('admin'))
        else:
            flash("Incorrect password")
    else:
        flash("Invalid user")

    return redirect(url_for('login'))

