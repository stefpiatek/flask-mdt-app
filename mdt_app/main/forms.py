from wtforms import (StringField, BooleanField, DateField, SubmitField,
                     HiddenField, ValidationError, SelectField)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Regexp
from datetime import date

from flask_wtf import FlaskForm

from ..models import Meeting, Patient, Case, Action, User

# query select functions


def get_meetings():
    return (Meeting.query.filter(Meeting.date >= str(date.today()))
                         .filter(Meeting.is_cancelled == False)
                         .order_by(Meeting.date))


def get_consultants():
    return (User.query.filter_by(is_consultant=True)
                      .order_by(User.username))

# Forms

class CaseForm(FlaskForm):
    meeting = QuerySelectField('Meeting date', query_factory=get_meetings,
                               get_label='date', blank_text='---',
                               allow_blank=True, validators=[DataRequired()])
    consultant = QuerySelectField('Consultant', query_factory=get_consultants,
                               get_label='username', blank_text='---',
                               allow_blank=True, validators=[DataRequired()])
    mdt_vcmg = SelectField('MDT or VGMG',
                           choices= [('MDT','MDT'), ('VCMG', 'VCMG')],
                           validators=[DataRequired()])
    submit = SubmitField('Submit')


class MeetingForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d')
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
    date_of_birth = DateField('Date of birth', format='%Y-%m-%d',
                              validators=[DataRequired()])
    id = HiddenField('Primary key')
    submit = SubmitField('Submit')

    def validate_hospital_number(self, field):
        existing = Patient.query.filter_by(hospital_number=field.data).first()
        if existing and int(self.id.data) != int(existing.id):
                raise ValidationError('Patient with hospital number '
                                      'already exists')