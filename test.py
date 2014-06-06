#!/usr/bin/env python
import os

from random import randrange
from sys import hexversion

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import impression

from impression.mixin import safe_commit
from impression.models import User, ApiKey, Content, File, Setting

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
        impression.app.config["CACHE_TYPE"] = "null"
        # Use memory DB
        impression.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        impression.app.config['TESTING'] = True
        self.app = impression.app.test_client()

        # Drop and create DB.
        impression.db.drop_all(bind=[None])
        impression.db.create_all(bind=[None])
        safe_commit()

        key = '{0:02X}'.format(randrange(36**50))
        self.api_key = ApiKey(key=key, name='test-key')
        self.api_key.insert()
        self.s = TimestampSigner(key)

        hashed_password = generate_password_hash('password-123')

        # Create a user to update and delete later.
        self.user = User(name="Test User", email='test_user@impression.com', admin=True, openid='', password=hashed_password)
        self.user.insert()

        # Available Themes
        themes = ['Stock Bootstrap 3', 'amelia', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'lumen', 'readable', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti']
        syntax_themes = ['autumn.css', 'borland.css', 'bw.css', 'colorful.css', 'default.css', 'emacs.css', 'friendly.css', 'fruity.css', 'github.css', 'manni.css', 'monokai.css', 'murphy.css', 'native.css', 'pastie.css', 'perldoc.css', 'tango.css', 'trac.css', 'vim.css', 'vs.css', 'zenburn.css']

        # Create some system settings
        Setting(name='blog-title', type='str', system=True).insert()
        Setting(name='blog-copyright', type='str', system=True).insert()
        Setting(name='cache-timeout', type='int', system=True, value=0).insert()
        Setting(name='posts-per-page', type='int', system=True, value=4).insert()
        Setting(name='bootstrap-theme', type='str', system=True, value='yeti', allowed=json.dumps(themes)).insert()
        Setting(name='syntax-highlighting-theme', type='str', system=True, value='monokai.css', allowed=json.dumps(syntax_themes)).insert()
        Setting(name='custom-front-page', type='str', system=True).insert()

        safe_commit()

    def tearDown(self):
        impression.db.drop_all(bind=[None])

    def test_upload(self):
        filename = 'test.txt'
        the_file = os.path.join(impression.app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(the_file):
            os.unlink(the_file)

        post_data = {
            'file': (StringIO("This is a test file."), filename),
            'name': 'Test File',
            'user_id': self.user.id
        }
        rv = self.app.post('/upload_ajax', data=post_data, follow_redirects=True)
        self.assertEquals(rv.status_code, 200)
        data = json.loads(rv.data)
        print(data)
        self.assertEquals(data['messages'][0], 'The file was uploaded.')
        afile = File.get(data['id'])
        self.assertEquals(data['id'], afile.id)
        self.assertTrue(os.path.isfile(the_file))

        # Delete the file we uploaded
        os.unlink(the_file)

    def test_content_create(self):
        api_key = self.s.sign(self.api_key.name)

        '''
        CREATE
        '''
        post_data = {
            'title': 'This is a test page',
            'body': 'Blah blah blah',
            'type': 'post',
            'published': 1,
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
        user_id = self.user.id

        '''
        RETRIEVE
        '''

        # Create some content using the model directly...
        content = Content(title="Test Content", published=True, type="post", body="blah blah blah", user_id=self.user.id)
        content.insert()

        content1 = content.to_dict()

        content2 = Content(title="Test Content 2", published=True, type="post", body="blah blah blah", user_id=self.user.id)
        content2.insert()

        content2 = content2.to_dict()

        content3 = Content(title="Test Content 3", published=True, type="post", body="blah blah blah", user_id=self.user.id)
        content3.insert()

        content3 = content3.to_dict()

        content4 = Content(title="Test Content 4", published=True, type="post", body="blah blah blah", user_id=self.user.id)
        content4.insert()

        content4 = content4.to_dict()

        safe_commit()

        post_data = {
            'id': content.id
        }
        # retrieve the content. This should work fine.
        rv = self.app.post('/content_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['contents'][0])
        self.assertIsNotNone(data['messages'])

        content = Content.get(data['contents'][0]['id'])
        self.assertEquals(content.title, data['contents'][0]['title'])
        self.assertEquals(content.body, data['contents'][0]['body'])
        self.assertEquals(user_id, data['contents'][0]['user_id'])

        post_data = {
            'content_type': 'post',
            'page_size': 3
        }
        # retrieve the content. This should work fine.
        rv = self.app.post('/content_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])

        # There should be three posts.
        self.assertEquals(data['contents'][0]['title'], content4['title'])
        self.assertEquals(data['contents'][1]['title'], content3['title'])
        self.assertEquals(data['contents'][2]['title'], content2['title'])

        # And only three posts returned
        self.assertTrue(len(data['contents']) == 3)

        # Posts should be in the right order
        self.assertTrue(data['contents'][1]['published_on'] < data['contents'][0]['published_on'])

        self.assertIsNotNone(data['messages'])

        post_data = {
            'content_type': 'post',
            'current_page': 2,
            'page_size': 3
        }
        # retrieve the content. This should work fine.
        rv = self.app.post('/content_retrieve', data=post_data, follow_redirects=True)
        data = json.loads(rv.data)
        self.assertTrue(data['success'])

        # There should be one post.
        self.assertEquals(data['contents'][0]['title'], content1['title'])

        # And only one post returned
        self.assertTrue(len(data['contents']) == 1)

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
