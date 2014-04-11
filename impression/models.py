#! /usr/bin/env python
from impression import db
from mixin import OurMixin

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

class Page(OurMixin, db.Model):
    __tablename__ = 'pages'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=512))
    url = db.Column(db.VARCHAR(length=256))
    content = db.Column(db.TEXT())
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship("User", cascade='delete')
    published = db.Column(db.Boolean(), default=False, server_default='0')

class Post(OurMixin, db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    title = db.Column(db.VARCHAR(length=512))
    url = db.Column(db.VARCHAR(length=256))
    content = db.Column(db.TEXT())
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship("User", cascade='delete')
    published = db.Column(db.Boolean(), default=False, server_default='0')

class Setting(OurMixin, db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.VARCHAR(length=128), nullable=False)
    value = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('int', 'str', 'bool', 'float'), nullable=False)
    allowed = db.Column(db.Text, nullable=True)

    @property
    def val(self):
        """
        Gets the value as the proper type.
        """
        return __builtins__[self.type](self.value)

class RoleType(OurMixin, db.Model):
    __tablename__ = 'role_types'
    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    name = db.Column(db.String(60))

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

class UserRole(OurMixin, db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.VARCHAR(length=36), primary_key=True)
    user_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship("User", backref="user_roles")
    role_type_id = db.Column(db.VARCHAR(length=36), db.ForeignKey('role_types.id', ondelete='CASCADE'), nullable=True)
    role_type = db.relationship("RoleType", backref="user_roles")
