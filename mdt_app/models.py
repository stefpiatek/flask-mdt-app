from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import date
from flask import current_app

from flask_login import UserMixin, AnonymousUserMixin

from . import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, unique=True)
    email = db.Column(db.String(100), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_confirmed = db.Column(db.Boolean(), default=False)
    is_consultant = db.Column(db.Boolean(), default=False)
    is_admin = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return '<User: {:s}>'.format(self.username)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True)
    comment = db.Column(db.String(255))
    is_cancelled = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return '<Meeting: {:s}>'.format(self.date)


class Case(db.Model):
    __tablename__ = 'cases'
    id = db.Column(db.Integer, primary_key=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_on = db.Column(db.Date, default=date.today)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    consultant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    mdt_vcmg = db.Column(db.String(10), default='MDT')
    outcome = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False)
    created_by = db.relationship('User', foreign_keys=created_by_id,
                                 uselist=False)
    consultant = db.relationship('User',
                 primaryjoin="and_(Case.consultant_id == User.id, " +
                             "User.is_consultant == True)",
                             uselist=False)
    patient = db.relationship('Patient', backref='cases',
                              order_by='Case.created_on')
    meeting = db.relationship('Meeting', backref='cases',
                              order_by='Case.created_on')


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    hospital_number = db.Column(db.String(20), nullable=False, unique=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return ('<Patient: '
                '{l_name:s}, {f_name:s}>').format(f_name=self.first_name,
                                                  l_name=self.last_name.upper())


class Action(db.Model):
    __tablename__ = 'actions'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'))
    action = db.Column(db.String(255), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_completed = db.Column(db.Boolean(), default=False)
    case = db.relationship('Case', backref='actions',
                           order_by=id)
    assigned_to = db.relationship('User', foreign_keys=assigned_to_id,
                                  uselist=False)

    def __repr__(self):
        return '<Action:{:s}>'.format(self.id)
