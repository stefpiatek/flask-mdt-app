import pytest
from datetime import date, timedelta

from mdt_app.models import *


class TestMeetingModel():
    def test_repr(self):
        meet = Meeting(date=date(2017, 9, 20))

        assert meet.__repr__() == '<Meeting: 2017-09-20>'

    def test_date_repr(self):
        meet = Meeting(date=date(2017, 9, 20))

        assert meet.date_repr == '20-Sep-2017'


class TestCaseModel():
    def test_repr(self):
        patient = Patient(first_name='Jo', last_name='Tibbles')
        case = Case(id=1, patient=patient)

        assert case.__repr__() == '<Case: 1, <Patient: TIBBLES, Jo>>'

class TestPatientModel():
    def test_repr(self):
        patient = Patient(first_name='Jo', last_name='Tibbles')

        assert patient.__repr__() == '<Patient: TIBBLES, Jo>'

    def test_date_of_birth_date(self):
        birth_date = date(1950, 9, 20)
        patient = Patient(date_of_birth= birth_date)

        assert '20-Sep-1950' in patient.date_of_birth_repr

    def test_date_of_birth_age(self):
        birth_date = date.today() - timedelta(days=366*7)
        patient = Patient(date_of_birth=birth_date)

        assert '(7)' in patient.date_of_birth_repr


class TestActionModel():
    def test_repr(self):
        action = Action(id=1)

        assert action.__repr__() == '<Action: 1>'


class TestAttendeeModel():
    def test_repr(self):
        meeting = Meeting(date=date(2017, 9, 20))
        user = User(username='admin')
        attendee = Attendee(id=1, meeting=meeting, user=user)

        assert attendee.__repr__() == '<Attendee: 1 (2017-09-20, admin)>'