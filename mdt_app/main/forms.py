import datetime
from wtforms import (StringField, BooleanField, DateField, SubmitField,
                     HiddenField, ValidationError, SelectField, TextAreaField,
                     widgets)
from wtforms.ext.sqlalchemy.fields import (QuerySelectField,
                                           QuerySelectMultipleField)
from wtforms.validators import DataRequired, Length, Regexp, Optional
from wtforms import widgets
from datetime import date, timedelta

from flask_wtf import FlaskForm

from ..models import Meeting, Patient, Case, Action, User
from config import date_style

# query select functions


def get_meetings():
    """Get the next 20 non cancelled meetings from 2 weeks ago onwards"""
    earliest_date = str(date.today() - timedelta(days=14))
    return (Meeting.query.filter(Meeting.date >= earliest_date)
                         .filter(Meeting.is_cancelled == 'FALSE')
                         .order_by(Meeting.date)
                         .limit(20))


def get_consultants():
    """Get all users who are consultants"""
    return (User.query.filter_by(is_consultant=True)
                      .order_by(User.username))


def get_users():
    """Get all confirmed users"""
    return User.query.filter_by(is_confirmed=True).order_by(User.username)


# Forms

class CaseForm(FlaskForm):
    case_id = HiddenField()
    patient_id = HiddenField()
    meeting = QuerySelectField('MDT date', query_factory=get_meetings,
                               get_label='date_repr',
                               blank_text='---', allow_blank=True,
                               validators=[Optional()])
    add_meeting = DateField('Add new MDT date',
                            format=date_style['format'],
                            validators=[Optional()],
                            description=date_style['help'])
    consultant = QuerySelectField('Consultant', query_factory=get_consultants,
                                  get_label='initials', blank_text='---',
                                  allow_blank=True, validators=[DataRequired()])
    next_opa = DateField('Date of next OPA', format=date_style['format'],
                         validators=[Optional()],
                         description=date_style['help'])
    clinic_code = SelectField('Clinic code',
                              choices=[(code, code)
                                       for code in
                                       sorted(['', 'TJG1A', 'TJG2A', 'RH11A',
                                               'JO12A', 'JO11A', 'MHP02',
                                               'MHP2D'])],
                              validators=[Optional()])
    planned_surgery = StringField('Planned surgery',
                                  validators=[Length(0, 255)])
    surgery_date = DateField('Date of surgery', format=date_style['format'],
                             validators=[Optional()],
                             description=date_style['help'])
    medical_history = TextAreaField('Medical History',
                                    validators=[DataRequired()],
                                    filters=[lambda x: x.strip() if x
                                             else None])
    mdt_vcmg = SelectField('MDT or VGMG',
                           choices=[('MDT', 'MDT'), ('VCMG', 'VCMG')],
                           validators=[DataRequired()])
    question = TextAreaField('Question for MDT', validators=[DataRequired()],
                             filters=[lambda x: x.strip() if x else None])
    submit = SubmitField('Submit')

    def validate_meeting(self, field):
        if field.data:
            existing = (Case.query
                            .filter_by(meeting_id=field.data.id,
                                       patient_id=self.patient_id.data)
                            .first())
            if existing and int(self.case_id.data) != int(existing.id):
                raise ValidationError('Patient already has a case on this date')
            if self.add_meeting.data:
                raise ValidationError('Choose a MDT date or type one in')
        else:
            if not self.add_meeting.data:
                raise ValidationError('Choose a MDT date or type one in')

    def validate_add_meeting(self, field):
        existing = Meeting.query.filter_by(date=field.data).first()
        if existing:
            raise ValidationError('Meeting already exists on that day')


class CaseEditForm(CaseForm):
    discussion = TextAreaField('Discussion',
                               filters=[lambda x: x.strip() if x else None])
    action = StringField('Action', validators=[Length(0, 255)])
    action_to = QuerySelectField('Assigned to', query_factory=get_users,
                                  get_label='username', blank_text='---',
                                  allow_blank=True)
    no_actions = BooleanField('No actions required')
    submit = SubmitField('Submit')

    def validate_no_actions(self, field):
        if field.data:
            existing = Action.query.filter_by(case_id=self.case_id.data).all()
            if existing or self.action.data:
                raise ValidationError('Actions already exist for this case')

    def validate_action(self, field):
        if ((field.data and self.action_to.data and self.discussion.data) or
             (not field.data and not self.action_to.data)):
            pass
        elif field.data and not self.discussion.data:
            raise ValidationError('Discussion and action should both be filled')
        else:
            raise ValidationError('Action and action by must both be filled in')


class AttendeeForm(FlaskForm):
    user = QuerySelectMultipleField('Members',
                                    query_factory=get_users,
                                    get_label=lambda x: str(('{} {}'
                                                             ).format(x.f_name,
                                                                      x.l_name))
                                    )
    comment = TextAreaField('Meeting comments',
                            filters=[lambda x: x.strip() if x else None])
    submit = SubmitField('Save attendees')


class MeetingForm(FlaskForm):
    date = DateField('Date', format=date_style['format'],
                     description=date_style['help'],
                     validators=[DataRequired()])
    comment = StringField('Comment', filters=[lambda x: x.strip() if x
                                              else None])
    is_cancelled = BooleanField('Meeting cancelled?')
    id = HiddenField('Primary key')
    submit = SubmitField('Submit')

    def validate_date(self, field):
        existing = Meeting.query.filter_by(date=field.data).first()
        if existing and int(self.id.data) != int(existing.id):
            raise ValidationError('Meeting on this date already exists')


class PatientForm(FlaskForm):
    hospital_number = StringField('Hospital number',
                                  validators=[Length(8), DataRequired()],
                                  filters=[lambda x: x.strip().upper() if x
                                           else None])
    first_name = StringField('First name',
                             validators=[Length(2, 255), DataRequired()],
                             filters=[lambda x: x.strip().title()
                                      if x else None])
    last_name = StringField('Last name',
                            validators=[Length(2, 255), DataRequired()],
                            filters=[lambda x: x.strip().upper() if x
                                     else None])
    date_of_birth = DateField('Date of birth', format=date_style['format'],
                              validators=[DataRequired()],
                              description=date_style['help'])
    sex = SelectField('Sex',
                      choices=[('', '---'), ('F', 'Female'),
                               ('M', 'Male')],
                      validators=[DataRequired()])
    id = HiddenField('Primary key')
    submit = SubmitField('Submit')

    def validate_hospital_number(self, field):
        existing = (Patient.query
                           .filter_by(hospital_number=field.data)
                           .first())
        if existing and int(self.id.data) != int(existing.id):
            raise ValidationError('Patient with hospital number already exists')

    def validate_date_of_birth(self, field):
        existing = (Patient.query
                           .filter_by(first_name=self.first_name.data,
                                      last_name=self.last_name.data,
                                      date_of_birth=field.data)
                           .first())
        if existing and int(self.id.data) != int(existing.id):
            raise ValidationError('Patient with same first name, last name '
                                  'and date of birth already exists')

class ActionForm(FlaskForm):
    id = HiddenField('Primary key')
    action = StringField('Action', validators=[Length(1, 255), DataRequired()])
    assigned_to = QuerySelectField('Assigned to', query_factory=get_users,
                                   get_label='username', blank_text='---',
                                   allow_blank=True,
                                   validators=[DataRequired()])
    is_completed = BooleanField('Completed?')
    submit = SubmitField('Submit')