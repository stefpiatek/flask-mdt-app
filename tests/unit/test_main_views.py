import pytest

from flask import url_for
from pytest_flask import fixtures
from flask_login import login_user, current_user, logout_user

from mdt_app.models import *
from mdt_app.main.forms import *

@pytest.mark.usefixtures('client_class', 'db_session', 'populate_db')
class TestIndex:
    def setup(self):
        user1 = User.query.first()
        login_user(user1)

    def test_page_load(self):
        assert self.client.get(url_for('main.index')).status_code == 200


@pytest.mark.developing
@pytest.mark.usefixtures('client_class', 'db_session', 'populate_db')
class TestCaseList:
    def setup(self):
        self.meeting = Meeting.query.first()

    def test_page_load(self):
        request = self.client.get(url_for('main.case_list'))

        assert request.status_code == 200

        # Cases are listed with patient name
        assert b"PATIENT" in request.data
        assert b"ENTRY" in request.data

    def test_meeting_filter(self):
        request = self.client.get(url_for('main.case_list',
                                          meeting=self.meeting.date))
        html = str(request.data).replace('\\n', '').replace('\\t', '')

        # Cases are listed with patient name, without cases for 16th Oct)
        assert "PATIENT" in html
        assert "DUMMY" in html
        assert "16-Oct-2050" not in html

        # status bar
        assert "33% Discussed" in html
        assert "To be discussed: 2 / 3" in html
        assert "to be actioned: 1 / 3" in html
        assert "& actioned: 0 / 3" in html

    def test_push_cases_no_future(self):
        request = self.client.get(url_for('main.case_list',
                                          meeting=self.meeting.date,
                                          push_cases=1))

        assert b'no meetings exist after this one' in request.data

    def test_push_cases_patient_clash(self):
        early_meeting = Meeting.query.filter_by(date='2050-10-16').first()
        request = self.client.get(url_for('main.case_list',
                                          meeting=early_meeting.date,
                                          push_cases=1))

        assert b'was not moved as patient also has a case' in request.data

    def test_push_cases_success(self, db_session):
        all_meetings = Meeting.query.all()
        new_meeting = Meeting(date='2050-12-30',
                              id=all_meetings[-1].id + 1)
        db_session.add(new_meeting)
        db_session.commit()
        request = self.client.get(url_for('main.case_list',
                                          meeting=self.meeting.date,
                                          push_cases=1))

        assert b'Case for patient Third DUMMY was moved to ' in request.data


@pytest.mark.usefixtures('client_class', 'db_session', 'populate_db')
class TestCaseCreate:
    def setup(self):
        meeting = Meeting.query.filter_by(date='2050-10-16').first()
        consultant = User.query.filter_by(initials='AC').first()
        self.form = CaseForm(case_id=-1,
                             patient_id=1,
                             meeting=meeting.id,
                             consultant=consultant.id,
                             mdt_vcmg='MDT',
                             medical_history='another set of medical history',
                             question='another question here',
                             clinic_code='')

    def test_page_load(self):
        req_pass = self.client.get(url_for('main.case_create', patient_id=1))
        req_no_id = self.client.get(url_for('main.case_create', patient_id=''))

        assert req_pass.status_code == 200
        # title
        assert b"Cases for Test PATIENT 12345678" in req_pass.data
        # flashed message
        assert b"Date of birth (age):" in req_pass.data

        assert req_no_id.status_code == 404, 'no id, page not found'

    # login works within scope of function but not in the view
    # need to make a login fixture?
    @pytest.mark.xfail
    def test_case_add(self):
        # login user for created_by
        user1 = User.query.first()
        login_user(user1)
        print(current_user)
        # request
        request = self.client.post(url_for('main.case_create', patient_id=1),
                                   data=self.form.data)


        assert request.status_code == 302

        assert b"another set of medical history" in request.data
