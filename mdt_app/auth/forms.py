from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask_wtf import FlaskForm

from ..models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                                   Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    f_name = StringField('First name',
                         validators=[DataRequired(), Length(1, 64),
                                     Regexp('^[A-Za-z]+$', 0,
                                            'Names can only have letters')])
    l_name = StringField('Last name',
                         validators=[DataRequired(), Length(1, 64)])
    username = StringField('Username',
                           validators=[DataRequired(), Length(1, 64),
                                       Regexp('^[a-z0-9]+$', 0,
        'Usernames must have only lower-case letters and numbers')])
    is_consultant = BooleanField('Are you a consultant?')
    initials = StringField('Initials (required for consultants)',
                                validators=[Length(0, 10)])

    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

    def validate_initials(self, field):
        print(field.data)
        print(self.initials.data)
        if self.is_consultant.data and field.data == '':
            raise ValidationError('Please fill in the initials field')



def get_users():
    return User.query.order_by(User.username)


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    user = QuerySelectField('User', query_factory=get_users,
                               get_label='username', blank_text='---',
                               allow_blank=True, validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired()])
    submit = SubmitField('Reset Password')
