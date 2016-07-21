import json

from flask import (Blueprint, render_template, flash, request, redirect, url_for,
                   jsonify)
from flask_login import login_user, logout_user, login_required

from jinja2.exceptions import TemplateNotFound
from sqlalchemy import or_  # , and_

from impression.decorators import user_is, user_has, import_user
from impression.controls import (get_payload, render, get_setting, get_menu_items,
                                 render_admin)
from impression.utils import success, chunks
from impression.extensions import cache
from impression.forms import LoginForm
from impression.models import Role, Setting, User, Content
from impression.mixin import safe_commit, paginate, results_to_dict

main_controller = Blueprint('main_controller', __name__)


@main_controller.route('/')
# @cache.cached(timeout=1000)
def index():
    user_count = User.count()
    print(user_count)
    if user_count == 0:
        # Run setup wizard.
        print('Redirecting to setup.')
        return redirect(url_for('.setup'))

    custom_front_page = get_setting('custom-front-page', '')
    if custom_front_page:
        try:
            return render(custom_front_page)
        except TemplateNotFound:
            return render("error.html", title="Custom Front Page", error="You have configured a custom front page but the file ({}) was not found in your theme's template directory.".format(custom_front_page))

    return redirect('/blog/')


@main_controller.route('/blog', methods=['GET'])
@main_controller.route('/blog/', methods=['GET'])
@main_controller.route('/blog/<int:page>', methods=['GET'])
@main_controller.route('/tags/<tag>', methods=['GET'])
@main_controller.route('/tags/<tag>/<int:page>', methods=['GET'])
# @cache.cached(timeout=CACHE_TIMEOUT)
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
    return render('index.html', user=import_user(), posts=posts, current_page=page,
                  max_pages=max_pages, tag_chunks=tag_chunks, tag=tag,
                  menu_items=get_menu_items())


'''
CONTENT ROUTES
'''

@main_controller.route('/get_tags_in_use', methods=['GET'])
# @cache.cached(timeout=CACHE_TIMEOUT)
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


@main_controller.route('/search', methods=['POST'])
def search_page():
    payload = get_payload(request)
    search = payload.get('search')
    contents = Content.filter(or_(Content.body.ilike('%{}%'.format(search)),
                                  Content.tags.ilike('%{}%'.format(search)),
                                  Content.title.ilike('%{}%'.format(search))))\
        .filter(Content.published == True).all()

    return render('search.html', user=import_user(), contents=contents,
                  menu_items=get_menu_items())


@main_controller.route('/page/<string:content_id>', methods=['GET'])
# @cache.cached(timeout=CACHE_TIMEOUT)
def render_page(content_id):
    content = Content.get(content_id)
    if not content:
        content = Content.filter(Content.slug == content_id).first()

    return render(content.template, user=import_user(),
                  content=content, menu_items=get_menu_items())


@main_controller.route('/post/<string:content_id>', methods=['GET'])
# @cache.cached(timeout=CACHE_TIMEOUT)
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
    return render(content.template, user=import_user(), content=content, tag_chunks=tag_chunks, menu_items=get_menu_items())


@main_controller.route('/content_retrieve', methods=['POST'])
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
            return_value['contents'] = results_to_dict(
                contents, camel_case=True)

    return jsonify(return_value)


@main_controller.route('/setup', methods=["GET", "POST"])
def setup():
    import shlex
    import subprocess
    user_count = User.count()
    # print(user_count)
    if user_count > 0:
        # We already have a user. No running setup.
        return redirect(url_for('.index'))

    if request.method == 'POST':
        payload = get_payload(request)
        if payload.get('email') and payload.get('password'):

            user = User(username=payload.get('email'),
                        password=payload.get('password'),
                        firstname=payload.get('firstname'),
                        lastname=payload.get('lastname'))

            my_role = Role(name='admin')
            my_role.add_abilities('create_users', 'delete_users', 'create_content',
                                  'delete_content', 'upload_files', 'delete_files',
                                  'change_settings')

            user.add_roles('admin', 'superadmin')

            login_user(user)

            args = shlex.split("alembic history")
            p = subprocess.Popen(args, stdout=subprocess.PIPE)
            output, error = p.communicate()
            data = output.split('\n')
            latest_alembic = None
            for row in data:
                if "(head)" in row:
                    cols = row.split(" ")
                    latest_alembic = cols[2].strip()

            if latest_alembic:
                print("Stamping with latest Alembic revision: %s" %
                      latest_alembic)
                args = shlex.split("alembic stamp %s" % latest_alembic)
                subprocess.Popen(args, stdout=subprocess.PIPE)

            # Available Themes
            themes = ['Stock Bootstrap 3', 'amelia', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly',
                      'lumen', 'readable', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti']
            syntax_themes = ['autumn.css', 'borland.css', 'bw.css', 'colorful.css', 'default.css', 'emacs.css', 'friendly.css', 'fruity.css', 'github.css',
                             'manni.css', 'monokai.css', 'murphy.css', 'native.css', 'pastie.css', 'perldoc.css', 'tango.css', 'trac.css', 'vim.css', 'vs.css', 'zenburn.css']

            # Create some system settings
            Setting(name='blog-title', vartype='str', system=True).insert()
            Setting(name='blog-copyright', vartype='str', system=True).insert()
            Setting(name='blog-theme', vartype='str',
                    system=True, value='impression').insert()
            Setting(name='posts-per-page', vartype='int',
                    system=True, value=4).insert()
            Setting(name='bootstrap-theme', vartype='str', system=True,
                    value='yeti', allowed=json.dumps(themes)).insert()
            Setting(name='syntax-highlighting-theme', vartype='str', system=True,
                    value='monokai.css', allowed=json.dumps(syntax_themes)).insert()
            Setting(name='custom-front-page',
                    vartype='str', system=True).insert()
            Setting(name='allowed-extensions', vartype='list', system=True,
                    value="['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tiff']").insert()
            Setting(name='upload-directory', vartype='str', system=True, value='uploads/').insert()
            Setting(name='max-file-size', vartype='int',
                    system=True, value=16777216).insert()
            safe_commit()
            flash("Initial Setup Complete", "success")
            return redirect(url_for('admin_controller.admin_settings'))

    return render('setup.html')


@main_controller.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).one()
        login_user(user)

        flash("Logged in successfully.", "success")
        return redirect(request.args.get("next") or url_for(".index"))

    return render_admin("login.html", form=form)


@main_controller.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for(".index"))


@main_controller.route("/restricted", methods=["GET", "POST"])
@login_required
@user_is('admin')
def restricted():
    return render_template("restricted.html")


@main_controller.route("/create_user")
@login_required
@user_has('create_users')
def create_user():
    return "You can only see this if you are logged in with 'create_users' permissions!", 200
