import datetime
from wtforms import (StringField, BooleanField, DateField, SubmitField,
                     HiddenField, ValidationError, SelectField, TextAreaField,
                     widgets)
from wtforms.ext.sqlalchemy.fields import (QuerySelectField,
                                           QuerySelectMultipleField)
from wtforms.validators import DataRequired, Length, Regexp, Optional
from datetime import date

from flask_wtf import FlaskForm

from ..models import Meeting, Patient, Case, Action, User
from config import date_style

# query select functions


def get_meetings():
    return (Meeting.query.filter(Meeting.date >= str(date.today()))
                         .filter(Meeting.is_cancelled == 'FALSE')
                         .order_by(Meeting.date))


def get_consultants():
    return (User.query.filter_by(is_consultant=True)
                      .order_by(User.username))


def get_users():
    return User.query.order_by(User.username)


# Forms


class CaseForm(FlaskForm):
    case_id = HiddenField('Primary key')
    patient_id = HiddenField('Patient key')
    meeting = QuerySelectField('Meeting date', query_factory=get_meetings,
                               get_label='date_repr',
                               blank_text='---', allow_blank=True,
                               validators=[DataRequired()])
    consultant = QuerySelectField('Consultant', query_factory=get_consultants,
                                  get_label='username', blank_text='---',
                                  allow_blank=True, validators=[DataRequired()])
    next_opa = DateField('Date of next OPA', format=date_style['format'],
                         validators=[Optional()],
                         description=date_style['help'])
    clinic_code = SelectField('Clinic code',
                              choices=[('', '---'), ('TE', 'Test'),
                                       ('MO', 'More')],
                              validators=[Optional()])
    planned_surgery = StringField('Planned surgery',
                                  validators=[Length(0, 255)])
    surgery_date = DateField('Date of surgery', format=date_style['format'],
                             validators=[Optional()],
                             description=date_style['help'])
    medical_history = TextAreaField('Medical History',
                                    validators=[DataRequired()])
    mdt_vcmg = SelectField('MDT or VGMG',
                           choices=[('MDT', 'MDT'), ('VCMG', 'VCMG')],
                           validators=[DataRequired()])
    question = TextAreaField('Question for MDT', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_meeting(self, field):
        existing = (Case.query
                        .filter_by(meeting_id=field.data.id,
                                   patient_id=self.patient_id.data)
                        .first())
        if not self.case_id.data:
            self.case_id.data = -1
        if existing and int(self.case_id.data) != int(existing.id):
            raise ValidationError('Patient already has a case on that date')


class CaseEditForm(CaseForm):
    discussion = TextAreaField('Discussion')
    action1 = StringField('Action #1', validators=[Length(0, 255)])
    action1_to = QuerySelectField('Action #1 by', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    action2 = StringField('Action #2', validators=[Length(0, 255)])
    action2_to = QuerySelectField('Action #2 by', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    action3 = StringField('Action #3', validators=[Length(0, 255)])
    action3_to = QuerySelectField('Action #3 by', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    action4 = StringField('Action #4', validators=[Length(0, 255)])
    action4_to = QuerySelectField('Action #4 by', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    action5 = StringField('Action #5', validators=[Length(0, 255)])
    action5_to = QuerySelectField('Action #5 by', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    submit = SubmitField('Submit')

    def validate_action1(self, field):
        if not field.data:
            field.data = None
        if field.data and field.data == self.action1_to.data:
            raise ValidationError('Action and action by must both be filled in')

    def validate_action2(self, field):
        if not field.data:
            field.data = None
        elif not self.action1.data:
            raise ValidationError('Fill out previous actions first')
        if field.data and field.data == self.action2_to.data:
            raise ValidationError('Action and action by must both be filled in')

    def validate_action3(self, field):
        if not field.data:
            field.data = None
        elif not (self.action1.data and self.action2.data):
            raise ValidationError('Fill out previous actions first')
        if field.data and field.data == self.action3_to.data:
            raise ValidationError('Action and action by must both be filled in')

    def validate_action4(self, field):
        if not field.data:
            field.data = None
        elif not (self.action1.data and self.action2.data
                  and self.action3.data):
            raise ValidationError('Fill out previous actions first')
        if field.data and field.data == self.action4_to.data:
            raise ValidationError('Action and action by must both be filled in')

    def validate_action5(self, field):
        if not field.data:
            field.data = None
        elif not (self.action1.data and self.action2.data
                  and self.action3.data and self.action4.data):
            raise ValidationError('Fill out previous actions first')
        if field.data and field.data == self.action5_to.data:
            raise ValidationError('Action and action by must both be filled in')


class AttendeeForm(FlaskForm):
    user = QuerySelectMultipleField('Usenames',
                                    query_factory=get_users,
                                    get_label='username')
    submit = SubmitField('Save attendees')


class MeetingForm(FlaskForm):
    date = DateField('Date', format='%d-%b-%Y',
                     description='DD-MMM-YYYY')
    comment = StringField('Comment', validators=[Length(0, 255)])
    is_cancelled = BooleanField('Meeting cancelled?')
    id = HiddenField('Primary key')
    submit = SubmitField('Submit')

    def validate_date(self, field):
        existing = Meeting.query.filter_by(date=field.data).first()
        if existing and int(self.id.data) != int(existing.id):
            raise ValidationError('Meeting on this date already exists')


class PatientForm(FlaskForm):
    hospital_number = StringField('Hospital number',
                                  validators=[Length(8, 20), DataRequired()])
    first_name = StringField('First name',
                             validators=[Length(2, 255), DataRequired()])
    last_name = StringField('Last name',
                            validators=[Length(2, 255), DataRequired()])
    date_of_birth = DateField('Date of birth', format=date_style['format'],
                              validators=[DataRequired()],
                              description=date_style['help'])
    id = HiddenField('Primary key')
    submit = SubmitField('Submit')

    def validate_hospital_number(self, field):
        existing = Patient.query.filter_by(hospital_number=field.data).first()
        if existing and int(self.id.data) != int(existing.id):
            raise ValidationError('Patient with hospital number already exists')

class ActionForm(FlaskForm):
    id = HiddenField('Primary key')
    action = StringField('Action', validators=[Length(1, 255), DataRequired()])
    assigned_to = QuerySelectField('Assigned_to', query_factory=get_users,
                                   get_label='username', blank_text='---',
                                   allow_blank=True,
                                   validators=[DataRequired()])
    is_completed = BooleanField('Completed?')
    submit = SubmitField('Submit')
