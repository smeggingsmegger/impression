#! ../env/bin/python
# -*- coding: utf-8 -*-

import pytest

from impression.models import db, User

create_user = False


@pytest.mark.usefixtures("testapp")
class TestModels:
    def test_user_save(self, testapp):
        """ Test Saving the user model to the database """

        admin = User(username="admin", password="supersafepassword")
        db.session.add(admin)
        db.session.commit()

        user = User.query.filter_by(username="admin").first()
        assert user is not None

    def test_user_password(self, testapp):
        """ Test password hashing and checking """

        admin = User(username="admin", password="supersafepassword")

        assert admin.username == 'admin'
        assert admin.check_password('supersafepassword')
