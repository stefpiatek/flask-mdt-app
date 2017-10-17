import pytest

from wtforms.validators import ValidationError

from mdt_app.main.forms import *
from mdt_app.models import *


@pytest.mark.usefixtures('db_session', 'populate_db')
class TestQuerySelectFunctions:
    def test_get_meetings(self):
        """returns future meetings that are not cancelled in order"""
        past = Meeting.query.filter_by(date='2010-11-15').first()
        cancelled = Meeting.query.filter_by(is_cancelled=True).first()
        meetings = get_meetings().all()

        assert meetings[0].date < meetings[1].date
        assert past not in meetings
        assert cancelled not in meetings

    def test_get_consultants(self):
        """returns only consultants in order"""
        consultants = get_consultants().all()
        not_consultant = User.query.filter_by(is_consultant=False).first()

        assert not_consultant not in consultants
        assert consultants[0].username < consultants[1].username

    def test_get_users(self):
        """returns confirmed users by username"""
        confirmed = get_users().all()
        unconfirmed = User.query.filter_by(is_confirmed=False).first()

        assert confirmed[0].username < confirmed[1].username
        assert unconfirmed not in confirmed


@pytest.mark.usefixtures('db_session', 'populate_db')
class TestCaseForm:
    def setup(self):
        meeting = Meeting.query.filter_by(date='2050-10-16').first()
        consultant = User.query.filter_by(initials='AC').first()
        self.form = CaseForm(case_id=-1,
                             patient_id=1,
                             meeting=meeting,
                             consultant=consultant,
                             mdt_vcmg='MDT',
                             medical_history='medical history here',
                             question='question here')

    def test_validate_meeting(self):
        """
        Custom validation failures:
        - Case already exists for that patient on that date
        - meeting and add_meeting both filled in
        - no meeting or add_meeting data
        """
        existing_date = Meeting.query.filter_by(date='2050-10-30').first()
        existing_case = CaseForm(data=self.form.data,
                                 meeting=existing_date)
        double_meeting_in = CaseForm(data=self.form.data,
                                     add_meeting='2050-11-15',)
        no_meeting = CaseForm(data=self.form.data,
                              meeting=None)

        assert self.form.validate() is True

        with pytest.raises(ValidationError):
            no_meeting.validate_meeting(no_meeting.meeting)

        with pytest.raises(ValidationError):
            existing_case.validate_meeting(existing_case.meeting)

        with pytest.raises(ValidationError):
            double_meeting_in.validate_meeting(double_meeting_in.meeting)

    def test_validate_add_meeting(self):
        """Validate if meeting does not already exist on that date"""
        existing_date = Meeting.query.first()
        new_meeting = CaseForm(data=self.form.data,
                               meeting=None,
                               add_meeting='2050-11-15')
        existing_meeting = CaseForm(data=self.form.data,
                                    meeting=None,
                                    add_meeting=existing_date.date)

        assert new_meeting.validate() is True

        with pytest.raises(ValidationError):
            existing_meeting.validate_add_meeting(existing_meeting.add_meeting)


@pytest.mark.usefixtures('db_session', 'populate_db')
class TestCaseEditForm:
    def setup(self):
        meeting = Meeting.query.filter_by(date='2050-10-16').first()
        consultant = User.query.filter_by(initials='AC').first()
        self.user1 = User.query.first()
        self.form = CaseForm(case_id=2,
                             patient_id=1,
                             meeting=meeting,
                             consultant=consultant,
                             mdt_vcmg='MDT',
                             medical_history='medical history here',
                             question='question here')

    def test_validate_no_actions(self):
        """Validate only if no actions exist or are in the form"""
        no_problems = CaseEditForm(data=self.form.data,
                                   no_actions=True)
        form_actions = CaseEditForm(data=self.form.data,
                                    no_actions=True,
                                    action='dummy action',
                                    action_to=self.user1)
        saved_actions = CaseEditForm(data=self.form.data,
                                     no_actions=True,
                                     case_id=1)

        assert no_problems.validate() is True

        with pytest.raises(ValidationError):
            form_actions.validate_no_actions(form_actions.no_actions)

        with pytest.raises(ValidationError):
            saved_actions.validate_no_actions(saved_actions.no_actions)

    def test_validate_action(self):
        user1 = User.query.first()
        """
        Validate passes if
        - action and action_to are blank
        - action, action_to and discussion are filled

        Validate fails if
        - one of discussion, action or action_to are blank
        """
        no_data = CaseEditForm(data=self.form.data)
        no_problems = CaseEditForm(data=self.form.data,
                                   discussion='discussed',
                                   action='dummy action',
                                   action_to=self.user1)
        no_discussion = CaseEditForm(data=no_problems.data,
                                     discussion=None)
        no_action = CaseEditForm(data=no_problems.data,
                                 action=None)
        no_action_to = CaseEditForm(data=no_problems.data,
                                    action_to=None)

        assert no_data.validate() is True
        no_data.validate_action(no_data.action)

        assert no_problems.validate() is True
        no_problems.validate_action(no_problems.action)

        with pytest.raises(ValidationError):
            no_discussion.validate_action(no_discussion.action)

        with pytest.raises(ValidationError):
            no_action.validate_action(no_action.action)

        with pytest.raises(ValidationError):
            no_action_to.validate_action(no_action_to.action)


@pytest.mark.usefixtures('db_session', 'populate_db')
class TestMeetingForm:
    """Validate if meeting on that date doesn't have the same id"""
    def setup(self):
        self.new_meeting = MeetingForm(id=-1,
                                       date='2050-11-15')

    def test_validate_date(self):
        existing_meeting = Meeting.query.first()
        last_meeting = Meeting.query.all()[-1]
        create_meeting = MeetingForm(data=self.new_meeting.data)
        edit_meeting = MeetingForm(data=self.new_meeting.data,
                                   id=existing_meeting.id)
        create_date_clash = MeetingForm(data=self.new_meeting.data,
                                        date=existing_meeting.date)
        edit_date_clash = MeetingForm(id=last_meeting.id + 1,
                                        date=existing_meeting.date)

        assert create_meeting.validate() is True
        create_meeting.validate_date(create_meeting.date)

        assert edit_meeting.validate() is True
        edit_meeting.validate_date(edit_meeting.date)

        with pytest.raises(ValidationError):
            create_date_clash.validate_date(create_date_clash.date)

        with pytest.raises(ValidationError):
            edit_date_clash.validate_date(edit_date_clash.date)


@pytest.mark.usefixtures('db_session', 'populate_db')
class TestPatientForm:
    def setup(self):
        self.patient = PatientForm(id=-1,
                                   hospital_number='15975346',
                                   first_name='New',
                                   last_name='PATIENT',
                                   date_of_birth='1987-12-05',
                                   sex='F')
        self.existing_patients = Patient.query.all()

    def test_validate_hospital_number(self):
        exists = self.existing_patients[0]
        last_patient = self.existing_patients[-1]
        new_patient = PatientForm(data=self.patient.data)
        edit_patient = PatientForm(data=self.patient.data,
                                   id=exists.id)
        create_patient_clash = PatientForm(data=self.patient.data,
            hospital_number=exists.hospital_number)
        edit_patient_clash = PatientForm(data=create_patient_clash.data,
                                         id=last_patient.id + 1)

        assert new_patient.validate() is True
        new_patient.validate_hospital_number(new_patient.hospital_number)

        assert edit_patient.validate() is True
        edit_patient.validate_hospital_number(edit_patient.hospital_number)

        with pytest.raises(ValidationError):
            create_patient_clash.validate_hospital_number(
                create_patient_clash.hospital_number)

        with pytest.raises(ValidationError):
            edit_patient_clash.validate_hospital_number(
                edit_patient_clash.hospital_number)

    def test_validate_date_of_birth(self):
        """Patient can't match another with same name and date of birth"""
        exists = self.existing_patients[0]
        last_patient = self.existing_patients[-1]

        create_clash = PatientForm(data=self.patient.data,
                                   first_name=exists.first_name,
                                   last_name=exists.last_name,
                                   date_of_birth=exists.date_of_birth)
        edit_clash = PatientForm(data=create_clash.data,
                                 id=last_patient.id)

        with pytest.raises(ValidationError):
            create_clash.validate_date_of_birth(
                create_clash.date_of_birth)

        with pytest.raises(ValidationError):
            edit_clash.validate_date_of_birth(
                edit_clash.date_of_birth)
