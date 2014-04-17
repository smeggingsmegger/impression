#!/usr/bin/env python
from random import randrange
from sys import hexversion

import impression
from impression.mixin import safe_commit
from impression.models import User, ApiKey, Content

from itsdangerous import TimestampSigner

import simplejson as json
if hexversion < 0x02070000:
    import unittest2 as unittest
else:
    import unittest

import warnings

from werkzeug.security import generate_password_hash, check_password_hash

warnings.simplefilter("ignore")

class impressionTestCase(unittest.TestCase):

    def setUp(self):
        impression.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        impression.app.config['TESTING'] = True
        self.app = impression.app.test_client()

        # Drop and create DB.
        impression.db.drop_all(bind=[None])
        impression.db.create_all(bind=[None])

        key = '{0:02X}'.format(randrange(36**50))
        self.api_key = ApiKey(key=key, name='test-key')
        self.api_key.insert()
        self.s = TimestampSigner(key)
        safe_commit()

        hashed_password = generate_password_hash('password-123')

        # Create a user to update and delete later.
        self.user = User(name="Test User", email='test_user@impression.com', admin=True, openid='', password=hashed_password)
        self.user.insert()

        safe_commit()

    def tearDown(self):
        impression.db.drop_all(bind=[None])

    def test_content_create(self):
        api_key = self.s.sign(self.api_key.name)

        '''
        CREATE
        '''
        post_data = {
            'title': 'This is a test page',
            'body': 'Blah blah blah',
            'type': 'post',
            'user_id': self.user.id
        }
        # Try to create the content with no API key
        rv = self.app.post('/content_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # Create the content. This should work fine.
        post_data['api_key'] = api_key
        rv = self.app.post('/content_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['id'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'The content was created.')
        content_id = data['id']

        # Make sure that we can grab the content from the DB.
        content = Content.get(content_id)
        self.assertIsNotNone(content)
        self.assertEquals(content.title, post_data['title'])

        # Try to create the same content again. This should fail.
        rv = self.app.post('/content_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'That post or page exists already.')

        # Clean up!
        content.delete()
        safe_commit()

        # Create the content. This should work fine.
        post_data['api_key'] = api_key
        post_data['type'] = 'page'
        rv = self.app.post('/content_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['id'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'The content was created.')
        content_id = data['id']

        # Make sure that we can grab the content from the DB.
        content = Content.get(content_id)
        self.assertIsNotNone(content)
        self.assertEquals(content.title, post_data['title'])

        # Try to create the same content again. This should fail.
        rv = self.app.post('/content_create', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'That post or page exists already.')

        # Clean up!
        content.delete()
        safe_commit()

    def test_content_retrieve(self):
        api_key = self.s.sign(self.api_key.name)
        user_id = self.user.id

        '''
        RETRIEVE
        '''

        # Create some content using the model directly...
        content = Content(title="Test Content", type="post", body="blah blah blah", user_id=self.user.id)
        content.insert()
        safe_commit()

        post_data = {
            'id': content.id
        }
        # Try to retrieve the content with no API key
        rv = self.app.post('/content_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # retrieve the content. This should work fine.
        post_data['api_key'] = api_key
        rv = self.app.post('/content_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['content'])
        self.assertIsNotNone(data['messages'])

        content = Content.get(data['content']['id'])
        self.assertEquals(content.title, data['content']['title'])
        self.assertEquals(content.body, data['content']['body'])
        self.assertEquals(user_id, data['content']['user_id'])

    def test_user_create(self):
        api_key = self.s.sign(self.api_key.name)

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
        self.assertTrue(data['id'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'The user was created.')
        user_id = data['id']

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

        # Clean up!
        user.delete()
        safe_commit()

    def test_user_retrieve(self):
        api_key = self.s.sign(self.api_key.name)

        '''
        RETRIEVE
        '''
        post_data = {
            'id': self.user.id
        }
        # Try to retrieve the user with no API key
        rv = self.app.post('/user_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # Retrieve the user. This should work fine.
        post_data['api_key'] = api_key
        rv = self.app.post('/user_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['user'])
        self.assertEquals(data['user']['name'], 'Test User')

    def test_user_update(self):
        api_key = self.s.sign(self.api_key.name)

        '''
        UPDATE
        '''
        post_data = {
            'name': 'New Person',
            'email': 'newperson@impression.com',
            'password': 'newperson123',
            'id': self.user.id
        }
        # Try to update the user with no API key
        rv = self.app.post('/user_update', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])

        # update the user. This should work fine.
        post_data['api_key'] = api_key
        rv = self.app.post('/user_update', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['user'])
        self.assertIsNotNone(data['messages'])
        self.assertEquals(data['messages'][0], 'The user was updated.')

        # Make sure that we can grab the user from the DB.
        user = User.get(self.user.id)
        self.assertIsNotNone(user)
        self.assertEquals(data['user']['name'], 'New Person')
        self.assertEquals(user.name, 'New Person')
        self.assertTrue(check_password_hash(user.password, 'newperson123'))

    def test_user_delete(self):
        api_key = self.s.sign(self.api_key.name)

        '''
        DELETE
        '''
        # Delete the user.
        post_data = {
            'id': self.user.id
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
        user = User.get(self.user.id)
        self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()
