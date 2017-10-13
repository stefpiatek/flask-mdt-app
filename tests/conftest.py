import pytest

from flask.ext.sqlalchemy import event

from mdt_app import create_app
from mdt_app import db as _db

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