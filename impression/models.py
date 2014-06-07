#! /usr/bin/env python
import json
from datetime import datetime

from impression import db
from impression.mixin import OurMixin
from impression.utils import success #, failure

class ApiKey(OurMixin, db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    key = db.Column(db.VARCHAR(length=512))
    name = db.Column(db.VARCHAR(length=512))

class Log(OurMixin, db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    action = db.Column(db.VARCHAR(length=5120))
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship("User", cascade='delete')

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
    parser = db.Column(db.Enum('markdown', 'html', 'textile', 'mediawiki'), nullable=False, default='markdown')
    url = db.Column(db.VARCHAR(length=256))
    header_image = db.Column(db.VARCHAR(length=256))
    preview = db.Column(db.TEXT())
    slug = db.Column(db.VARCHAR(length=512))
    body = db.Column(db.TEXT())
    tags = db.Column(db.TEXT())
    menu_item = db.Column(db.Boolean(), default=False, server_default='0')
    template = db.Column(db.VARCHAR(length=256), default="post.html")
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User")
    published = db.Column(db.Boolean(), default=False, server_default='0')
    published_on = db.Column(db.DateTime(), nullable=False, default=datetime.now)


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
            import markdown
            content = markdown.markdown(value, extensions=['codehilite', 'fenced_code'])
        elif self.parser == 'textile':
            import textile
            content = textile.textile(value)
        elif self.parser == 'mediawiki':
            from creole import creole2html
            content = creole2html(unicode(value))

        return content

class Setting(OurMixin, db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=128), nullable=False)
    human_name = db.Column(db.TEXT(), nullable=True, default='', server_default='')
    value = db.Column(db.TEXT(), nullable=True, default='', server_default='')
    vartype = db.Column(db.Enum('int', 'str', 'bool', 'float'), nullable=False)
    allowed = db.Column(db.Text, nullable=True)
    system = db.Column(db.Boolean(), default=False, server_default='0')
    description = db.Column(db.TEXT(), nullable=True, default='', server_default='')

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
        return __builtins__[self.vartype](self.value)

class Tag(OurMixin, db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=64), nullable=False)

class RoleType(OurMixin, db.Model):
    __tablename__ = 'role_types'
    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.String(60))

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

class User(OurMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))
    password = db.Column(db.String(200))
    admin = db.Column(db.Boolean(), default=False, server_default='0')
    active = db.Column(db.Boolean(), default=True, server_default='1')

    def __repr__(self):
        return "User: {} - {} - {}".format(self.id, self.name, self.email)

    def validate(self):
        return_value = success()
        not_unique = User.filter(User.email == self.email).count()
        if not_unique:
            return_value['success'] = False
            return_value['messages'].append("That user exists already.")
        if not self.email:
            return_value['success'] = False
            return_value['messages'].append("An email address is required to create a user.")

        return return_value

class UserRole(OurMixin, db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User")
    role_type_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('role_types.id', ondelete='CASCADE'), nullable=True)
    role_type = db.relationship("RoleType", backref="user_roles")
