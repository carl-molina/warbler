"""User View tests."""

# run these tests like:
#
# FLASK_DEBUG=False python -m unittest test_user_views.py

import os
from unittest import TestCase

from bs4 import BeautifulSoup

from models import Follow, LikedMessages, Message, User, db

# BEFORE we import our app, let's set an environmental variable to use a
# different database for tests (we need to do this before we import our app,
# since that will have already connected to the database).

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables once for
# all tests --- in each test, we'll delete the data and create fresh new clean
# test data.)

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)
        u4 = User.signup("u4", "u4@email.com", "password", None)

        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id
        self.u4_id = u4.id

    def tearDown(self):
        db.session.rollback()

class UserListShowTestCase(UserBaseViewTestCase):
    # ^ this is subclassing UserBaseViewTestCase, but why??
    def setUp(self):
        super().setUp()
        m1 = Message(text="text", user_id=self.u1_id)
        db.session.add(m1)
        # ^ this adds 1 message instance (m1) to the db and connects it to u1

    def test_users_index(self):
        """Tests whether """
        with app.test_client() as c:
            with c.session_transaction() as sess:
                # ^ TODO: always remember to call it! c.session_transaction()
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/users')

            self.assertIn('@u1', str(resp.data))
            # ^ doesn't need to do 'html = resp.data(as_text=True)'
            # ^ simply because we're just trying to see if '@u1' is in resp.data
            # ^ still to note though: we're coercing resp.data into a str type
            # ^ so it's basically the same as resp.data(as_text=True)

            self.assertIn('@u2', str(resp.data))
            self.assertIn('@u3', str(resp.data))
            self.assertIn('@u4', str(resp.data))

    def test_users_search(self):
        """Tests whether u1 shows up in search when searching '1'"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/users?q=1')
            # ^ this is when the current user uses the search bar to find a user
            # that has 1 in their username

            self.assertIn("@u1", str(resp.data))
            self.assertNotIn("@u2", str(resp.data))

    def test_user_show(self):
        """Tests whether u1 shows up in user profile page."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', str(resp.data))