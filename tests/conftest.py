import pytest

from flask.ext.sqlalchemy import event

from mdt_app import create_app
from mdt_app import db as _db
from mdt_app.models import *


@pytest.yield_fixture(scope='session')
def app(request):
    """An application for the tests."""
    _app = create_app('testing')
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope='session')
def db(app, request):
    """Session-wide test database."""

    # NOTE: app, is required to keep the db in the right Flask app context
    _db.app = app
    _db.create_all()

    yield _db

    # teardown
    _db.session.close()
    _db.drop_all()


@pytest.yield_fixture(scope='class')
def db_session(db):
    """
    Creates a new database session for a test. Note you must use this fixture
    if your test connects to db.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    session.begin_nested()

    # session is actually a scoped_session
    # for the `after_transaction_end` event, we need a session instance to
    # listen for, hence the `session()` call
    @event.listens_for(session(), 'after_transaction_end')
    def resetart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            session.expire_all()
            session.begin_nested()

    db.session = session

    yield session

    # teardown
    session.remove()
    transaction.rollback()
    connection.close()


@pytest.yield_fixture(scope='class')
def populate_db(db_session):
    user1 = User(id=1, f_name='first', l_name='user',
                 email='test@user.com', username='fuser',
                 password='test_pass', is_confirmed=True)
    user_unconfirmed = User(id=2, f_name='uncon', l_name='firmed',
                            email='unconfirmed@user.com', username='ufirmed',
                            password='test_pass', is_confirmed=False)
    consult1 = User(id=3, f_name='consultant', l_name='test',
                   email='consult@user.com', username='ctest',
                   password='test_pass', is_confirmed=True, is_consultant=True,
                   initials='TC')
    consult2 = User(id=4, f_name='another', l_name='consultant',
                   email='aconsult@user.com', username='aconsultant',
                   password='test_pass', is_confirmed=True, is_consultant=True,
                   initials='AC')
    db_session.add(user1)
    db_session.add(user_unconfirmed)
    db_session.add(consult1)
    db_session.add(consult2)


    patient1 = Patient(id=1, hospital_number=12345678,
                       first_name='Test', last_name='PATIENT',
                       date_of_birth='1988-10-09', sex='F')
    patient2 = Patient(id=2, hospital_number=98765432,
                       first_name='Second', last_name='ENTRY',
                       date_of_birth='1953-01-02', sex='M')
    patient3 = Patient(id=3, hospital_number=95765432,
                       first_name='Third', last_name='DUMMY',
                       date_of_birth='1952-10-21', sex='M')
    db_session.add(patient1)
    db_session.add(patient2)
    db_session.add(patient3)

    # App is only for use until ~2020 so will always be in the future
    meeting1 = Meeting(id=1, date='2050-10-30')
    meeting2 = Meeting(id=2, date='2050-10-23',
                       comment='cancelled as no consultant',
                       is_cancelled=True)
    meeting3 = Meeting(id=3, date='2050-10-16')
    past_meeting = Meeting(id=4, date='2010-11-15', comment='past')
    db_session.add(meeting1)
    db_session.add(meeting2)
    db_session.add(meeting3)
    db_session.add(past_meeting)

    case1 = Case(id=1,
                 created_by_id=1,
                 created_on='2017-10-15',
                 patient_id=1,
                 meeting_id=1,
                 consultant_id=3,
                 medical_history='first case medical history here',
                 question='question here',
                 status='DISC')
    case2 = Case(id=2,
                 created_by_id=1,
                 created_on='2017-09-15',
                 patient_id=2,
                 meeting_id=3,
                 consultant_id=3,
                 medical_history='second case medical history here',
                 question='question here',
                 status='TBD')
    case3 = Case(id=3,
                 created_by_id=1,
                 created_on='2017-09-16',
                 patient_id=3,
                 meeting_id=1,
                 consultant_id=3,
                 medical_history='third case medical history here',
                 question='question here',
                 status='TBD')
    case4 = Case(id=4,
                 created_by_id=1,
                 created_on='2017-09-15',
                 patient_id=2,
                 meeting_id=1,
                 consultant_id=3,
                 medical_history='fourth',
                 question='question here',
                 status='TBD')
    db_session.add(case1)
    db_session.add(case2)
    db_session.add(case3)
    db_session.add(case4)


    action1 = Action(id=1,
                     case_id=1,
                     action='this is something that you need to do',
                     assigned_to_id=1)
    action2 = Action(id=2,
                     case_id=1,
                     action='contact gp',
                     assigned_to_id=1)
    db_session.add(action1)
    db_session.add(action2)

    attendee1 = Attendee()

    db_session.commit()
