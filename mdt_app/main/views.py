from flask import render_template, redirect, request, url_for, flash
from datetime import date

from flask_login import login_required, current_user

from .. import db
from ..models import Case, Meeting, Patient, Action
from . import main
from .forms import MeetingForm, PatientForm, CaseForm

@main.route('/')
@main.route('/index')
@login_required
def index():
    return render_template('index.html', title='Welcome to the MDT App')

@main.route('/cases/')
@login_required
def case_list():
    """List cases, if fk, filter by meeting id

    :request meeting: meeting date to filter by
    """
    meeting_date = request.args.get('meeting')
    title='Cases'

    if meeting_date:
        cases = Case.query.join(Meeting).filter_by(date=meeting_date).all()
        title += ': {}'.format(meeting_date)
    else:
        cases = Case.query.all()
    return render_template('case_list.html', cases=cases, title=title)


@main.route('/cases/create/<patient_id>',  methods=['GET', 'POST'])
@login_required
def case_create(patient_id=None):
    """ List cases for date or patient and form to create new case for patient

    :request patient: patient hospital number to filter by
    """
    if not patient_id:
        flash('Patient details not given')
        return render_template('404.html', title='Page does not exist')
    patient = Patient.query.filter_by(id=patient_id).first()
    cases = Case.query.filter_by(patient_id=patient_id).all()
    form = CaseForm()
    if form.validate_on_submit():
        case = Case(meeting_id=form.meeting.data.id,
                    consultant_id=form.consultant.data.id,
                    patient_id=patient_id,
                    mdt_vcmg=form.mdt_vcmg.data,
                    created_on=date.today(),
                    created_by_id=current_user.id,
                    status='TBR')
        db.session.add(case)
        db.session.commit()
        flash(('New case added for {f_name} {l_name}'
               ).format(f_name=patient.first_name,
                       l_name=patient.last_name))
        return redirect(url_for('main.case_list'))
    return render_template('case_create.html', cases=cases, form=form,
                           title=('Cases for {f_name} {l_name}'
                                  ).format(f_name=patient.first_name,
                                           l_name=patient.last_name))


@main.route('/meetings/create', methods=['GET', 'POST'])
@login_required
def meeting_create():
    """Create new meeting

    set form id to -1 so the db entry id does not equal the form id
    """
    form = MeetingForm(id=-1)
    if form.validate_on_submit():
        meeting = Meeting(date=form.date.data,
                          comment=form.comment.data,
                          is_cancelled=form.is_cancelled.data)
        db.session.add(meeting)
        db.session.commit()
        flash('New Meeting added for {date}'.format(date=form.date.data))
        return redirect(url_for('main.meeting_list'))
    return render_template('meeting_form.html', form=form,
                           title='Create a New Meeting')


@main.route('/meetings/edit/<int:pk>', methods=['GET', 'POST'])
@login_required
def meeting_edit(pk):
    """Edit meeting entry"""
    meeting = Meeting.query.filter_by(id=pk).first()
    form = MeetingForm(date=meeting.date,
                       comment=meeting.comment,
                       is_cancelled=meeting.is_cancelled,
                       id=meeting.id)
    if form.validate_on_submit():
        meeting.date = form.date.data
        meeting.comment = form.comment.data
        meeting.is_cancelled = form.is_cancelled.data
        db.session.commit()
        flash('Meeting for {date} has been edited'.format(date=form.date.data))
        return redirect(url_for('main.meeting_list'))
    return render_template('meeting_form.html', form=form, title='Edit meeting')


@main.route('/meetings')
@login_required
def meeting_list():
    """List all meetings"""
    meetings = Meeting.query.all()
    return render_template('meeting_list.html', meetings=meetings,
                           title='Meetings')


@main.route('/patients/create', methods=['GET', 'POST'])
@login_required
def patient_create():
    """Create new patient entry

    set form id to -1 so the db entry id does not equal the form id
    strip out whitespace in character fields in form
    """
    form = PatientForm(id=-1)
    if form.validate_on_submit():
        # Remove whitespace from either side of string fields
        patient = Patient(hospital_number=form.hospital_number.data.strip(),
                          first_name=form.first_name.data.strip(),
                          last_name=form.last_name.data.strip(),
                          date_of_birth=form.date_of_birth.data)
        db.session.add(patient)
        db.session.commit()
        flash('New Patient added'
              ' ({l_name}, {f_name})'.format(f_name=patient.first_name,
                                             l_name=patient.last_name.upper()))
        return redirect(url_for('main.patient_list'))
    return render_template('patient_form.html', form=form,
                           title='Add a New Patient')


@main.route('/patients/edit/<int:pk>', methods=['GET', 'POST'])
@login_required
def patient_edit(pk):
    """Edit patient entry"""
    patient = Patient.query.filter_by(id=pk).first()
    form = PatientForm(hospital_number=patient.hospital_number,
                       first_name=patient.first_name,
                       last_name=patient.last_name,
                       date_of_birth=patient.date_of_birth,
                       id=patient.id)
    if form.validate_on_submit():
        patient.hospital_number = form.hospital_number.data.strip()
        patient.first_name = form.first_name.data.strip()
        patient.last_name = form.last_name.data.strip()
        patient.date_of_birth = form.date_of_birth.data
        db.session.commit()
        flash('Patient edited'
              ' ({l_name}, {f_name})'.format(f_name=patient.first_name,
                                             l_name=patient.last_name.upper()))
        return redirect(url_for('main.patient_list'))
    return render_template('patient_form.html', form=form, title='Edit Patient')


@main.route('/patients')
@login_required
def patient_list():
    """List all meetings"""
    patients = Patient.query.all()
    return render_template('patient_list.html', patients=patients,
                           title='Patients')