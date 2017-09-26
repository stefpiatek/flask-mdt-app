from flask import render_template, redirect, request, url_for, flash

from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .. import db
from ..models import User
from .forms import *
from ..decorators import admin_required


@auth.before_app_request
def before_request():
    """Redirects non-confirmed users requestion non auth or static"""
    if (current_user.is_authenticated
            and not current_user.is_confirmed
            and request.endpoint[:5] != 'auth.'
            and request.endpoint != 'static'):
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """Page for anonymous or unconfirmed user"""
    if current_user.is_anonymous or current_user.is_confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login by user.verify_password"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            # log user in, with remember me set to false
            login_user(user, False)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.', category='danger')
    return render_template('auth/login.html', form=form, title='Log in')


@auth.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out.', category='success')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Register user"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    f_name=form.f_name.data,
                    l_name=form.l_name.data,
                    initials=form.initials.data.upper())
        db.session.add(user)
        db.session.commit()
        flash('Before you can use the site,'
              'your account must be verified by an administrator',
              category='info')
        flash(('please email the administrator '
              'asking for your account ({user}) to be verified'
               ).format(user=user.username),
              category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, title='Register')


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', category='success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.', category='danger')
    return render_template("auth/change_password.html", form=form,
                           title='Change Password')


@auth.route('/reset_password', methods=['GET', 'POST'])
@admin_required
@login_required
def reset_password():
    """Admin reset other user password"""
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user.data.id).first()
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash(('Temporary password for "{user}" is "{password}".'
               ).format(user=user.username, password=form.password.data),
              category='info')
        return redirect(url_for('main.index'))
    return render_template("auth/change_password.html", form=form,
                           title='Change Password')
