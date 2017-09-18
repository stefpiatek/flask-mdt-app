from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import date
from flask import current_app

from flask_login import UserMixin, AnonymousUserMixin

from . import db, login_manager
from config import date_style



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(50), nullable=False)
    l_name = db.Column(db.String(50), nullable=False)
    initials = db.Column(db.String(10))
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
    date = db.Column(db.Date, unique=True, nullable=False)
    comment = db.Column(db.String(255))
    is_cancelled = db.Column(db.Boolean(), default=False)

    @property
    def date_repr(self):
        return self.date.strftime(date_style['format'])

    def __repr__(self):
        return '<Meeting: {}>'.format(self.date)


class Case(db.Model):
    __tablename__ = 'cases'
    id = db.Column(db.Integer, primary_key=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                                                        nullable=False)
    created_on = db.Column(db.Date, default=date.today)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'),
                                                     nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'),
                                                     nullable=False)
    consultant_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                                                        nullable=False)
    next_opa = db.Column(db.Date)
    clinic_code = db.Column(db.String(50))
    planned_surgery = db.Column(db.String(255))
    surgery_date = db.Column(db.Date)
    medical_history = db.Column(db.Text, nullable=False)
    question = db.Column(db.Text, nullable=False)
    discussion = db.Column(db.Text)
    mdt_vcmg = db.Column(db.String(10), default='MDT', nullable=False)
    status = db.Column(db.String(10), default='TBD', nullable=False)
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
    db.UniqueConstraint('patient_id', 'meeting_id', name='patient_per_meeting')

    def __repr__(self):
        return '<Case: {}, {}>'.format(self.id, self.patient)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    hospital_number = db.Column(db.String(20), nullable=False, unique=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(1), nullable=False)

    @property
    def date_of_birth_repr(self):
        today = date.today()
        birth_date = self.date_of_birth
        # age: take year and -1 if born later in year than current point in year
        age = (today.year - birth_date.year -
               ((today.month, today.day) < (birth_date.month, birth_date.day)))
        return ('{dob} ({age})'
                ).format(dob=birth_date.strftime(date_style['format']),
                         age=age)

    def __repr__(self):
        return ('<Patient: '
                '{l_name}, {f_name}>').format(f_name=self.first_name,
                                              l_name=self.last_name.upper())


class Action(db.Model):
    __tablename__ = 'actions'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                                                         nullable=False)
    is_completed = db.Column(db.Boolean(), default=False)

    case = db.relationship('Case', backref='actions',
                           order_by=id)
    assigned_to = db.relationship('User', foreign_keys=assigned_to_id,
                                  uselist=False)
    db.UniqueConstraint('case_id', 'action', name='action_per_case')

    def __repr__(self):
        return '<Action: {}>'.format(self.id)


class Attendee(db.Model):
    __tablename__ = 'attendees'
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'),
                                                     nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    meeting = db.relationship('Meeting', backref='attendees')
    user = db.relationship('User', backref='attendees')
    db.UniqueConstraint('user_id', 'meeting_id', name='user_per_meeting')

    def __repr__(self):
        return '<Attendee: {} ({}, {})>'.format(self.id, self.meeting.date,
                                                self.user.username)