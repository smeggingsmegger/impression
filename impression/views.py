import os
import json
from dateutil import parser
from datetime import datetime
from sqlalchemy import or_#, and_

from flask import redirect, request, url_for, g, jsonify, send_from_directory, flash, session
from flask.ext.themes2 import get_themes_list
from jinja2.exceptions import TemplateNotFound

from impression import app, cache
from impression.controls import render, render_admin, admin_required, key_or_admin_required, get_payload, make_slug, get_setting
from impression.mixin import paginate, results_to_dict, safe_commit
from impression.models import User, Content, File, Tag, Setting
from impression.utils import success, failure, chunks

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

CACHE_TIMEOUT = 0

'''
Before we process any request, let's do some things.
'''
@app.before_request
def before_request():
    g.user = None
    g.theme = get_setting('blog-theme', 'impression')
    g.bootstrap_theme = get_setting('bootstrap-theme', 'yeti')
    g.syntax_highlighting_theme = get_setting('syntax-highlighting-theme', 'monokai.css')
    g.blog_title = get_setting('blog-title', 'Blog Title')
    g.blog_copyright = get_setting('blog-copyright', 'Blog Copyright')
    global CACHE_TIMEOUT
    CACHE_TIMEOUT = get_setting('cache-timeout', 0)

    if 'userid' in session:
        g.user = User.get(session['userid'])
        try:
            if not g.user.active:
                g.user = None
        except AttributeError:
            g.user = None

'''
All routes go here.
'''
@app.route('/', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def index():
    custom_front_page = get_setting('custom-front-page', '')
    if custom_front_page:
        try:
            return render(custom_front_page)
        except TemplateNotFound:
            return render("error.html", title="Custom Front Page", error="You have configured a custom front page but the file ({}) was not found in your theme's template directory.".format(custom_front_page))

    return redirect('/blog/')

@app.route('/blog', methods=['GET'])
@app.route('/blog/', methods=['GET'])
@app.route('/blog/<int:page>', methods=['GET'])
@app.route('/tags/<tag>', methods=['GET'])
@app.route('/tags/<tag>/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def blog_index(page=1, tag=None):
    tag_chunks = []
    tags = json.loads(get_tags_in_use())
    if tags:
        if len(tags) > 16:
            tags = tags[:16]
        tag_chunks = chunks(tags, 4)

    limit = get_setting("posts-per-page", 4)

    posts = Content.filter(Content.published == True)\
                   .filter(Content.type == "post")\
                   .order_by(Content.published_on.desc())

    if tag:
        posts = posts.filter(Content.tags.contains(tag))

    posts, max_pages = paginate(posts, page, limit)
    return render('index.html', user=g.user, posts=posts, current_page=page, max_pages=max_pages, tag_chunks=tag_chunks, tag=tag, menu_items=get_menu_items())

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
        thumbnail_name = ''
        thumbnail_path = ''
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
                fname, fext = os.path.splitext(filename)
                ext = ext.lower()
                etype = ext.replace(".", "")
                if etype == 'jpg':
                    etype = 'jpeg'
                thumbnail_path = file + "_thumbnail" + ext
                thumbnail_name = fname + "_thumbnail" + ext
                im.save(thumbnail_path, etype)
            except (ImportError, IOError):
                width = 0
                height = 0

            afile = File(name=filename, path=path, thumbnail_name=thumbnail_name, thumbnail_path=thumbnail_path,\
                         user_id=payload.get('user_id'), size=os.path.getsize(path), width=width, height=height, mimetype=ufile.mimetype)
            afile.insert()
            safe_commit()
        return afile.id
    return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get_tags', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_tags():
    tags = [t.name for t in Tag.all()]
    return json.dumps(tags)

@app.route('/get_tags_in_use', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_tags_in_use():
    all_tags = {}
    contents = Content.filter(Content.published == True).all()
    for content in contents:
        tags = [t.strip() for t in content.tags.split(',') if t.strip()]
        for tag in tags:
            tag_count = all_tags.get(tag, 0)
            if tag_count:
                all_tags[tag] += 1
            else:
                all_tags[tag] = 1

    all_tags = sorted(all_tags, key=all_tags.get, reverse=True)

    return json.dumps(all_tags)

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_menu_items():
    items = []
    contents = Content.filter(Content.menu_item == True).filter(Content.published == True).all()
    for content in contents:
        items.append({'title': content.title, 'slug': content.slug})

    return items

'''
CONTENT ROUTES
'''
@app.route('/search', methods=['POST'])
def search_page():
    payload = get_payload(request)
    search = payload.get('search')
    contents = Content.filter(or_(Content.body.ilike('%{}%'.format(search)),\
                                  Content.tags.ilike('%{}%'.format(search)),\
                                  Content.title.ilike('%{}%'.format(search))))\
                      .filter(Content.published == True)\
                      .all()
    return render('search.html', user=g.user, contents=contents, menu_items=get_menu_items())

@app.route('/page/<string:content_id>', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def render_page(content_id):
    content = Content.get(content_id)
    if not content:
        content = Content.filter(Content.slug == content_id).first()
    return render(content.template, user=g.user, content=content, menu_items=get_menu_items())

@app.route('/post/<string:content_id>', methods=['GET'])
@cache.cached(timeout=CACHE_TIMEOUT)
def render_post(content_id):
    tag_chunks = []
    tags = json.loads(get_tags_in_use())
    if tags:
        if len(tags) > 16:
            tags = tags[:16]
        tag_chunks = chunks(tags, 4)
    content = Content.get(content_id)
    if not content:
        content = Content.filter(Content.slug == content_id).first()
    return render(content.template, user=g.user, content=content, tag_chunks=tag_chunks, menu_items=get_menu_items())

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

    published = json.loads(payload.get('published', 'false'))
    content.published = published

    menu_item = json.loads(payload.get('menu_item', 'false'))
    content.menu_item = menu_item

    if not editing:
        content.slug = make_slug(content.title)
    else:
        published_on = payload.get('published_on')
        if published_on:
            content.published_on = parser.parse(published_on)

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

@app.route('/admin/users/delete', methods=['POST'])
@key_or_admin_required
def delete_user():
    return_value = success('The user was deleted.')
    payload = get_payload(request)

    if not g.user or g.user.id != payload.get('id'):
        user = User.filter(User.id == payload.get('id')).first()
        if user:
            user.active = False
            user.insert()
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
    return render_admin('files_list.html', files=files)

@app.route('/admin/files/add', methods=['GET'])
@admin_required
def admin_files_add():
    return render_admin('file.html')

@app.route('/admin/files/delete', methods=['POST'])
@admin_required
def admin_files_delete():
    return_value = success('The file has been deleted.')
    payload = get_payload(request)
    afile = File.get(payload.get('id'))
    if afile:
        try:
            os.unlink(afile.path)
        except OSError:
            pass
        try:
            os.unlink(afile.thumbnail_path)
        except OSError:
            pass
        afile.delete()
        safe_commit()

        with app.app_context():
            cache.clear()
    else:
        return_value = failure('File not found.')

    return jsonify(return_value)

@app.route('/admin/pages/add', methods=['GET'])
@admin_required
def admin_pages_add():
    content = Content()
    content.published_on = datetime.now()
    content.body = ''
    content.title = ''
    content.tags = ''
    content.parser = 'markdown'
    content.type = 'page'
    content.user = g.user
    content.user_id = g.user.id
    return render_admin('content.html', user=g.user, content_type="Page", action="Add", content=content)

@app.route('/admin/pages/edit/<string:content_id>', methods=['GET'])
@admin_required
def admin_pages_edit(content_id):
    content = Content.get(content_id)
    return render_admin('content.html', user=g.user, content_type=content.type, action="Edit", content=content)

@app.route('/admin/pages', methods=['GET'])
@admin_required
def admin_pages_list():
    contents = Content.filter(Content.type == 'page').order_by(Content.published_on.desc()).all()
    return render_admin('content_list.html', contents=contents, content_type="Pages")

@app.route('/admin/posts/add', methods=['GET'])
@admin_required
def admin_posts_add():
    content = Content()
    content.published_on = datetime.now()
    content.body = ''
    content.title = ''
    content.tags = ''
    content.parser = 'markdown'
    content.type = 'post'
    content.user = g.user
    content.user_id = g.user.id

    return render_admin('content.html', user=g.user, content_type="Post", action="Add", content=content)

@app.route('/admin/posts/edit/<string:content_id>', methods=['GET'])
@admin_required
def admin_posts_edit(content_id):
    content = Content.get(content_id)
    return render_admin('content.html', user=g.user, content_type=content.type, action="Edit", content=content)

@app.route('/admin/posts', methods=['GET'])
@admin_required
def admin_posts_list():
    contents = Content.filter(Content.type == 'post').order_by(Content.published_on.desc()).all()
    return render_admin('content_list.html', contents=contents, content_type="Posts")

@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_users_list():
    users = User.filter(User.active == True).all()
    return render_admin('users_list.html', users=users, content_type="Pages")

@app.route('/admin/users/add', methods=['GET'])
@admin_required
def admin_users_add():
    user = User()
    user.id = ''
    user.name = ''
    user.email = ''
    return render_admin('user.html', user=user)

@app.route('/admin/users/edit/<string:user_id>', methods=['GET'])
@admin_required
def admin_users_edit(user_id=''):
    user = User.get(user_id)
    return render_admin('user.html', user=user)

@app.route('/admin/users/edit/post', methods=['POST'])
@admin_required
def admin_users_edit_post():
    payload = get_payload(request)
    user_id = payload.get('user_id')
    if user_id:
        user = User.get(user_id)
        return_value = success('All profile values have been updated.')
    else:
        user = User()
        user.admin = True
        user.active = True
        user.openid = ''
        user.insert()
        return_value = success('User created.')
        if not payload.get('password'):
            return jsonify(failure('You must set a password for new users'))
        if not payload.get('email'):
            return jsonify(failure('You must set an email for new users'))
        if not payload.get('name'):
            return jsonify(failure('You must set a name for new users'))

    for key in payload:
        if key == 'password':
            hashed_password = generate_password_hash(payload[key])
            setattr(user, key, hashed_password)
        elif key != 'user_id':
            setattr(user, key, payload[key])

    g.user.insert()
    safe_commit()

    with app.app_context():
        cache.clear()

    return jsonify(return_value)

@app.route('/admin/settings', methods=['GET'])
@admin_required
def admin_settings():
    available_themes =[x.identifier for x in get_themes_list() if x.identifier != 'admin']
    settings = Setting.all()
    for setting in settings:
        if setting.name == 'blog-theme':
            setting.allowed = json.dumps(available_themes)
    return render_admin('settings.html', settings=settings)

@app.route('/admin/content/delete', methods=['POST'])
@admin_required
def admin_content_delete():
    return_value = success('The content has been deleted.')
    payload = get_payload(request)
    content = Content.get(payload.get('id'))
    if content:
        content.delete()
        safe_commit()

        with app.app_context():
            cache.clear()
    else:
        return_value = failure('Content not found.')

    return jsonify(return_value)

@app.route('/admin/settings/post', methods=['POST'])
@admin_required
def admin_settings_post():
    return_value = success('All settings have been updated.')
    payload = get_payload(request)

    for key in payload:
        setting = Setting.filter(Setting.name == key).first()
        setting.value = payload[key]
        setting.insert()

    safe_commit()

    with app.app_context():
        cache.clear()

    return jsonify(return_value)

@app.route('/admin', methods=['GET'])
@app.route('/admin/', methods=['GET'])
@admin_required
def admin():
    return render_admin('index.html', user=g.user)

@app.route('/logout', methods=['GET'])
def logout():
    session['userid'] = None
    return render_admin('login.html')

@app.route('/login', methods=['GET'])
def login():
    if g.user and g.user.admin:
        return redirect(url_for('admin'))
    return render_admin('login.html')

@app.route('/post_login', methods=['POST'])
def post_login():
    payload = get_payload(request)
    user = User.filter(User.active == True).filter(User.email == payload.get('email')).first()
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

