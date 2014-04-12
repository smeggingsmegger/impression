#!/usr/bin/env python
from random import randrange
from sys import hexversion

import impression
from impression.mixin import safe_commit
from impression.models import User, ApiKey

import simplejson as json
if hexversion < 0x02070000:
    import unittest2 as unittest
else:
    import unittest

import warnings

from werkzeug.security import generate_password_hash

warnings.simplefilter("ignore")

class impressionTestCase(unittest.TestCase):

    def setUp(self):
        impression.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        impression.app.config['TESTING'] = True
        self.app = impression.app.test_client()

        # Drop and create DB.
        impression.db.drop_all(bind=[None])
        impression.db.create_all(bind=[None])

        key = '{:02X}'.format(randrange(36**50))
        self.api_key = ApiKey(key=key, name='test-key')
        self.api_key.insert()
        safe_commit()

        hashed_password = generate_password_hash('password-123')

        # Create some users directly. We will test making them through the interface later.
        user = User(name="Test1 User1", email='test_user1@impression.com', admin=True, openid='', password=hashed_password)
        user.insert()

        user = User(name="Test3 User3", email='test_user3@impression.com', admin=True, openid='', password=hashed_password)
        user.insert()

        user = User(name="Mr. NoAdmin", email='no_admin@impression.com', admin=False, openid='', password=hashed_password)
        user.insert()

    def tearDown(self):
        impression.db.drop_all(bind=[None])

    def test_user_CRUD(self):
        api_key = self.api_key.key

        '''
        CREATE
        '''
        post_data = {
            'name': 'Testy McTesterson',
            'email': 'testy@impression.com',
            'password': 'test1234',
        }
        # Try to create the user with no API key
        rv = self.app.post('/user_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # Create the user. This should work fine.
        post_data['api_key'] = api_key
        rv = self.app.post('/user_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['user_id'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'The user was created.')
        user_id = data['user_id']

        # Make sure that we can grab the user from the DB.
        user = User.get(user_id)
        self.assertIsNotNone(user)
        self.assertEquals(user.name, 'Testy McTesterson')

        # Try to create the same user again. This should fail.
        rv = self.app.post('/user_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'That user exists already.')

        '''
        DELETE
        '''
        # Delete the user.
        post_data = {
            'id': user_id,
        }
        # Try to delete the user with no API key
        rv = self.app.post('/user_delete', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # Removing should work now.
        post_data['api_key'] = api_key
        rv = self.app.post('/user_delete', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        user = User.get(user_id)
        self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()
