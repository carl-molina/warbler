"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase

from models import db, User, Message, Follow
# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from flask import session
from flask_bcrypt import Bcrypt

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

db.drop_all()
db.create_all()

bcrypt = Bcrypt()
PASSWORD = bcrypt.generate_password_hash("password", rounds=5).decode("utf-8")

class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        u1_message = Message(text="Test")
        u1.messages.append(u1_message)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_message_model(self):
        """Tests that user1 model has 1 message. """

        u1 = User.query.get(self.u1_id)

        self.assertEqual(len(u1.messages), 1)
        self.assertNotEqual(len(u1.messages), 0)

    # NOTE: can't test this since there's no check constraint in Message model
    # def test_user_invalid_message(self):
    #     """Tests invalid text message. """

    #     u1 = User.query.get(self.u1_id)

    #     u1_message_2 = Message(text="")
    #     u1.messages.append(u1_message_2)
    #     db.session.commit()

    #     # self.assertEqual("ERROR:  zero-length delimited identifier", u1_message_2)
    #     # TODO: double quotes are for naming something
    #     # TODO: use single quotes on psql

    def test_user2_no_message(self):
        """Tests that user2 model has 0 messages. """

        u2 = User.query.get(self.u2_id)

        self.assertEqual(len(u2.messages), 0)
        self.assertNotEqual(len(u2.messages), 1)

    def test_user_has_liked_message(self):
        """Tests that user1 model has 1 liked message. """

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u2.liked.append(u1.messages[0])

        db.session.commit()

        self.assertEqual(len(u2.liked), 1)
        self.assertNotEqual(len(u2.liked), 0)


