import json

from ast import literal_eval
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from impression.mixin import OurMixin, db
from impression.utils import success

from sqlalchemy.ext.associationproxy import association_proxy
# from impression.utils import uuid


def _role_find_or_create(r):
    role = Role.query.filter_by(name=r).first()
    if not(role):
        role = Role(name=r)
        role.insert()
    return role


user_role_table = db.Table('user_roles',
                           db.Column(
                               'user_id', db.VARCHAR(36),
                               db.ForeignKey('users.id')),
                           db.Column(
                               'role_id', db.VARCHAR(36),
                               db.ForeignKey('roles.id'))
                           )

role_abilities_table = db.Table('role_abilities',
                              db.Column(
                                  'role_id', db.VARCHAR(36),
                                  db.ForeignKey('roles.id')),
                              db.Column(
                                  'ability_id', db.VARCHAR(36),
                                  db.ForeignKey('abilities.id'))
                              )


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


class Role(OurMixin, db.Model):

    """
    Subclass this for your roles
    """
    __tablename__ = 'roles'
    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.String(120), unique=True)
    abilities = db.relationship(
        'Ability', secondary=role_abilities_table, backref='roles')

    def __init__(self, name):
        self.name = name.lower()
        # self.id = uuid()
        super(Role, self).__init__()

    def add_abilities(self, *abilities):
        for ability in abilities:
            existing_ability = Ability.query.filter_by(
                name=ability).first()
            if not existing_ability:
                existing_ability = Ability(ability)
                existing_ability.insert()
                # safe_commit()
                #  db.session.commit()
            self.abilities.append(existing_ability)

    def remove_abilities(self, *abilities):
        for ability in abilities:
            existing_ability = Ability.query.filter_by(name=ability).first()
            if existing_ability and existing_ability in self.abilities:
                self.abilities.remove(existing_ability)

    def __repr__(self):
        return '<Role {}>'.format(self.name)

    def __str__(self):
        return self.name


class Ability(OurMixin, db.Model):

    """
    Subclass this for your abilities
    """
    __tablename__ = 'abilities'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.String(120), unique=True)

    def __init__(self, name):
        self.name = name.lower()
        # self.id = uuid()
        super(Ability, self).__init__()

    def __repr__(self):
        return '<Ability {}>'.format(self.name)

    def __str__(self):
        return self.name


class ApiKey(OurMixin, db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    key = db.Column(db.VARCHAR(length=512))
    name = db.Column(db.VARCHAR(length=512))


class Log(OurMixin, db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    action = db.Column(db.VARCHAR(length=5120))
    user_id = db.Column(db.VARCHAR(length=36),
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    user = db.relationship("User", cascade='delete')


class User(UserMixin, OurMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    username = db.Column(db.String())
    firstname = db.Column(db.String(32))
    lastname = db.Column(db.String(32))
    password = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True, server_default='1')

    _roles = db.relationship(
        'Role', secondary=user_role_table, backref='users')
    type = db.Column(db.String(50))

    roles = association_proxy('_roles', 'name', creator=_role_find_or_create)

    def __init__(self, **kwargs):
        # A bit of duplication here keeps the kwargs being
        # set but encrypts the password.
        for k, v in kwargs.items():
            if k != 'password':
                setattr(self, k, v)
            else:
                self.set_password(v)

        OurMixin.__init__(self)
        UserMixin.__init__(self)

    def validate(self):
        return_value = success()
        not_unique = User.filter(User.username == self.username).count()
        if not_unique:
            return_value['success'] = False
            return_value['messages'].append("That user exists already.")
        if not self.email:
            return_value['success'] = False
            return_value['messages'].append("An email address is required to create a user.")

        return return_value

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, value):
        return check_password_hash(self.password, value)

    def is_authenticated(self):
        if isinstance(self, AnonymousUserMixin):
            return False
        else:
            return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        if isinstance(self, AnonymousUserMixin):
            return True
        else:
            return False

    def add_roles(self, *roles):
        self.roles.extend([role for role in roles if role not in self.roles])

    def remove_roles(self, *roles):
        self.roles = [role for role in self.roles if role not in roles]

    def has_role(self, role):
        return True if role in self.roles else False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {}:{}>'.format(self.id, self.username)


class Setting(OurMixin, db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=128), nullable=False)
    section = db.Column(db.VARCHAR(length=128), nullable=False,
                        default='main', server_default='main')
    human_name = db.Column(db.TEXT(), nullable=True,
                           default='', server_default='')
    value = db.Column(db.TEXT(), nullable=True, default='', server_default='')
    vartype = db.Column(db.Enum('int', 'str', 'bool', 'float', 'list'), nullable=False)
    allowed = db.Column(db.Text, nullable=True)
    system = db.Column(db.Boolean(), default=False, server_default='0')
    description = db.Column(db.TEXT(), nullable=True,
                            default='', server_default='')

    @property
    def title(self):
        if self.human_name:
            return self.human_name
        else:
            return self.name.replace('-', ' ').title()

    @property
    def choices(self):
        return json.loads(self.allowed)

    @property
    def val(self):
        """
        Gets the value as the proper type.
        """
        if self.vartype == 'list':
            return list(literal_eval(self.value))
        else:
            return __builtins__[self.vartype](self.value)


class Tag(OurMixin, db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=64), nullable=False)


class File(OurMixin, db.Model):
    __tablename__ = 'files'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=256), nullable=False)
    path = db.Column(db.VARCHAR(length=512), nullable=True)
    thumbnail_name = db.Column(db.VARCHAR(length=256), nullable=True)
    thumbnail_path = db.Column(db.VARCHAR(length=512), nullable=True)
    width = db.Column(db.Integer(), default=0, server_default='0')
    height = db.Column(db.Integer(), default=0, server_default='0')
    size = db.Column(db.Integer(), default=0, server_default='0')
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User")
    mimetype = db.Column(db.VARCHAR(length=256), nullable=False)


class CustomField(OurMixin, db.Model):
    __tablename__ = 'custom_fields'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    content_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('content.id', ondelete='CASCADE'), nullable=False)
    content = db.relationship("Content", backref="contents", cascade='delete')
    type = db.Column(db.VARCHAR(length=64), nullable=False)
    key = db.Column(db.VARCHAR(length=256), nullable=False)
    value = db.Column(db.TEXT(), nullable=False)
    sort_order = db.Column(db.Integer(), default=1000, server_default='1000')


class Content(OurMixin, db.Model):
    __tablename__ = 'content'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    title = db.Column(db.VARCHAR(length=512))
    type = db.Column(db.Enum('post', 'page'), nullable=False)
    parser = db.Column(db.Enum('markdown', 'html', 'textile', 'mediawiki', 'rst'), nullable=False, default='markdown')
    url = db.Column(db.VARCHAR(length=256))
    header_image = db.Column(db.VARCHAR(length=256))
    preview = db.Column(db.TEXT())
    slug = db.Column(db.VARCHAR(length=512))
    body = db.Column(db.TEXT())
    tags = db.Column(db.TEXT())
    menu_item = db.Column(db.Boolean(), default=False, server_default='0')
    template = db.Column(db.VARCHAR(length=256), default="post.html")
    user_id = db.Column(db.VARCHAR(length=36),
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    user = db.relationship("User", cascade='delete')
    published = db.Column(db.Boolean(), default=False, server_default='0')
    published_on = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    theme = db.Column(db.VARCHAR(length=256))

    def validate(self):
        return_value = success()
        not_unique = Content.filter(Content.title == self.title).count()
        if not_unique:
            return_value['success'] = False
            return_value['messages'].append('That post or page exists already.')
        if not self.title:
            return_value['success'] = False
            return_value['messages'].append("A title is required to create a post or a page.")

        return return_value

    def human_created_on(self):
        return self.created_on.strftime("%m/%d/%Y %I:%M %p")

    def human_published_on(self):
        return self.published_on.strftime("%m/%d/%Y %I:%M %p")

    @property
    def parsed(self):
        return self.parse('body')

    @property
    def previewed(self):
        return self.parse('preview')

    def parse(self, to_parse):
        content = ''
        value = getattr(self, to_parse)
        if self.parser == 'html':
            content = value
        elif self.parser == 'markdown':
            try:
                import markdown
                content = markdown.markdown(value, extensions=['markdown.extensions.codehilite',
                                                               'markdown.extensions.fenced_code',
                                                               'markdown.extensions.tables'])
            except ImportError:
                content = value
                print('Markdown parser not installed. Try `pip install Markdown`')

        elif self.parser == 'textile':
            try:
                import textile
                content = textile.textile(value)
            except ImportError:
                content = value
                print('Markdown parser not installed. Try `pip install textile`')

        elif self.parser == 'mediawiki':
            try:
                from creole import creole2html
                content = creole2html(unicode(value))
            except ImportError:
                content = value
                print('Markdown parser not installed. Try `pip install python-creole`')

        return content
