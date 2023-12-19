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
    """Test cases for user show lists and deleting profile."""
    def setUp(self):
        super().setUp()
        m1 = Message(text="text", user_id=self.u1_id)
        db.session.add(m1)
        # ^ this adds 1 message instance (m1) to the db and connects it to u1

    def test_users_index(self):
        """Tests for signed in user and shows list of users."""

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
        """Tests whether u1 shows up in search when searching '1'."""

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

    def test_users_show_no_authentication(self):
        """Tests for redirect from /users to homepage if not logged in."""

        with app.test_client() as c:
            # Don't have anyone sign in to session; simulate non-logged in user.
            resp = c.get('/users', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Happening?', str(resp.data))

    def test_single_user_show_no_authentication(self):
        """Tests for redirect from /users/user_id to homepage if not logged in.
        """

        with app.test_client() as c:

            resp = c.get(f'/users/{self.u1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            self.assertIn('Happening?', str(resp.data))

    def test_user_delete_profile(self):
        """Tests for deleting profile and redirecting to signup."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/users/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.', str(resp.data))

    def test_user_delete_profile_no_authentication(self):
        """Tests if user profile can be deleted when user not logged in."""

        with app.test_client() as c:
            resp = c.post('/users/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertIn("Happening?", str(resp.data))


class UserProfileViewTestCase(UserBaseViewTestCase):
    """Test cases for user profile features."""

    def test_view_profile_form(self):
        """Tests for signed in user authorized to enter /users/profile route."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users/profile")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Your Profile', str(resp.data))

    def test_view_profile_form_no_authentication(self):
        """Tests for non-logged in user entering /users/profile route."""

        with app.test_client() as c:

            resp = c.get("/users/profile", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Happening?", str(resp.data))

    def test_edit_profile(self):
        """Tests for signed in user editing their user profile."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/users/profile",
                data={
                    "username": "UpdatedUser",
                    "email": "test@test.com",
                    "password": "password",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@UpdatedUser", str(resp.data))

    def test_edit_profile_invalid_email(self):
        """Tests for invalid email while editing user profile."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                '/users/profile',
                data={
                    "username": "test",
                    "email": "test",
                    "password": "password",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Invalid email address', str(resp.data))

    def test_edit_profile_invalid_password(self):
        """Tests for invalid password when logged in user edits user profile."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                '/users/profile',
                data={
                    "username": "test",
                    "email": "test@test.com",
                    "password": "wrongpassword",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid password!", str(resp.data))


class UserLikeTestCase(UserBaseViewTestCase):
    def setUp(self):
        super().setUp()
        m1 = Message(text="text", user_id=self.u2_id)
        db.session.add(m1)
        db.session.flush()
        k1 = LikedMessages(user_id=self.u1_id, message_id=m1.id)
        db.session.add(k1)
        db.session.commit()

        self.m1_id = m1.id

    def test_user_show_with_likes(self):
        """Tests for user profile page w/ added liked message count."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}')

            self.assertEqual(resp.status_code, 200)

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            self.assertIn("1", found[3].text)
            # ^ Tests for a count of 1 like

    def test_remove_like(self):
        """Tests removing like from current user's liked messages."""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f'/messages/{self.m1_id}/liked',
                data={
                    "location": f"/messages/{self.m1_id}"
                    },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("bi-star", str(resp.data))
            self.assertNotIn("bi-star-fill", str(resp.data))

            likes = LikedMessages.query.filter(
                LikedMessages.message_id == self.m1_id).all()
            self.assertEqual(len(likes), 0)


class UserFollowingViewTestCase(UserBaseViewTestCase):
    def setUp(self):
        super().setUp()

        # u1 followed by u2 and u3
        # u2 followed by u1

        f1 = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id
        )

        f2 = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u3_id
        )

        f3 = Follow(
            user_being_followed_id=self.u2_id,
            user_following_id=self.u1_id
        )

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_user_show_with_follows(self):
        """Tests current user's detail page along with their follower count."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', str(resp.data))

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            # Test for a count of 1 following
            self.assertIn("1", found[1].text)
            # Test for a count of 2 followers
            self.assertIn("2", found[2].text)