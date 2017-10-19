import pytest
from datetime import datetime

from pytest_flask import fixtures
from flask_login import current_user, login_user

from mdt_app.models import User


@pytest.mark.usefixtures('client_class', 'db_session', 'populate_db')
class TestUserModel():
    def setup(self):
        self.user = User(f_name='test', l_name='user', is_confirmed=True,
                         username='testuser', email='test@user.com',
                         password='woop')

    def test_password_setter(self):
        u = User(password='cat')
        assert u.password_hash is not None

    def test_no_password_getter(self):
        u = User(password='cat')
        with pytest.raises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        assert u.verify_password('cat') is True
        assert u.verify_password('dog') is False

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        assert u.password_hash != u2.password_hash

    def test_repr(self):
        u = User(username='Geoff')
        assert u.__repr__() == '<User: Geoff>'

    def test_load_user(self):
        user1 = User.query.first()
        login_user(user1)

        assert User.load_user(user1.id) == user1
        assert current_user == user1