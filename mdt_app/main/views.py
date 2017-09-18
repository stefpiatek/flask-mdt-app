from flask import render_template, redirect, request, url_for, flash
from datetime import date

from flask_login import login_required, current_user

from .. import db
from ..models import Case, Meeting, Patient, Action, Attendee, User
from . import main
from .forms import *


@main.route('/index')
def index():
    return render_template('index.html', title='Welcome to the MDT App')

@main.route('/')
@main.route('/cases/',  methods=['GET', 'POST'])
@login_required
def case_list():
    """List cases, if meeting date then filter by this and add attendee form

    :request meeting: meeting date to filter by
    """
    meeting_date = request.args.get('meeting')
    title = 'All cases'
    if meeting_date:
        meeting = Meeting.query.filter_by(date=meeting_date).first()
        case_query = Case.query.filter_by(meeting=meeting)
        attendees = Attendee.query.filter_by(meeting=meeting).all()
        attendee_list = [attendee.user for attendee in attendees]
        attendee_form = AttendeeForm(data={'user': attendee_list})
        title = 'Meeting: {}'.format(meeting.date_repr)
        counts = {stat.lower(): (Case.query
                                     .filter_by(status=stat, meeting=meeting)
                                     .count())
                  for stat in
                  ['TBD', 'COMP', 'DISC']}
        # For a case to be complete, it must be discussed so add together
        case_count = len(case_query.all())
        if case_count:
            counts['percent_discussed'] = int(100 / case_count *
                                              (counts['disc'] + counts['comp']))
    else:
        case_query = Case.query
        attendee_form = None
        counts = None
        attendees = None
    cases = (case_query.join(Meeting)
                       .order_by(Meeting.date.desc())
                       .all())
    if request.method == 'POST' and attendee_form.validate_on_submit():
        print('form', attendee_form.user)
        form_attendees = attendee_form.user.data
        for row_attendee in attendees:
            # remove users in database that are not in form data
            if not any(row_attendee.user.username == form_user.username
                       for form_user in form_attendees):
                db.session.delete(row_attendee)
                db.session.commit()
        for form_user in form_attendees:
            # if form user not in database, add them
            if not any(form_user.username == row_attendee.user.username
                       for row_attendee in attendees):
                new_attendee = Attendee(meeting=meeting,
                                        user=form_user)
                db.session.add(new_attendee)
        db.session.commit()
        return redirect(url_for('case_list.html', cases=cases, title=title,
                                counts=counts, attendee_form=attendee_form,
                                attendees=attendees))
    return render_template('case_list.html', cases=cases, title=title,
                           counts=counts, attendee_form=attendee_form,
                           attendees=attendees)


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
    cases = (Case.query
                 .filter_by(patient_id=patient_id)
                 .join(Meeting)
                 .order_by(Meeting.date.desc())
                 .all())
    form = CaseForm(patient_id=patient_id, case_id=-1)
    if form.validate_on_submit():
        case = Case(meeting_id=form.meeting.data.id,
                    consultant_id=form.consultant.data.id,
                    patient_id=patient_id,
                    next_opa=form.next_opa.data,
                    clinic_code=form.clinic_code.data,
                    planned_surgery=form.planned_surgery.data,
                    surgery_date=form.surgery_date.data,
                    medical_history=form.medical_history.data,
                    mdt_vcmg=form.mdt_vcmg.data,
                    question=form.question.data,
                    created_on=date.today(),
                    created_by_id=current_user.id,
                    status='TBD')
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


@main.route('/cases/edit/<patient_id>/<case_id>',  methods=['GET', 'POST'])
@login_required
def case_edit(patient_id=None, case_id=None):
    """ List cases for date or patient and form to create new case for patient

    :request patient: patient hospital number to filter by
    """
    if not (patient_id and case_id):
        flash('Patient or case details not given')
        return render_template('404.html', title='Page does not exist')
    patient = Patient.query.filter_by(id=patient_id).first()
    cases = (Case.query
                 .filter_by(patient_id=patient_id)
                 .join(Meeting)
                 .order_by(Meeting.date.desc())
                 .all())
    case = Case.query.filter_by(id=case_id).first()
    actions = (Action.query.filter_by(case_id=case_id)
                           .order_by(Action.form_field)
                           .all())
    action_list = ['action1', 'action2', 'action3', 'action4', 'action5']
    form = CaseEditForm(obj=case,
                        case_id=case_id)
    if request.method == 'GET':
        if actions:
            # actions exist so populate the form
            for act_model in actions:
                form[act_model.form_field].data = act_model.action
                form[act_model.form_field + '_to'].data = act_model.assigned_to
        elif case.status == 'COMP':
            form.no_actions.data = True
    elif form.validate_on_submit():
        # actions added or changed in form, revert to DISC
        # if stay the same or removed, do nothing
        new_form_actions = not all(form[act].data in (db_act.action
                                                      for db_act in actions)
                                   or form[act].data is None
                                   for act in action_list)
        if form.no_actions.data:
            case.status = 'COMP'
        elif not form.discussion.data:
            case.status = 'TBD'
        elif new_form_actions or not actions:
            case.status = 'DISC'
        # save form data for cases
        if form.meeting.data:
            case.meeting_id = form.meeting.data.id
        else:
            new_date = Meeting(date=form.add_meeting.data)
            db.session.add(new_date)
            db.session.commit()
            flash('MDT meeting added for {}'.format(new_date.date_repr))
            added_meeting = (Meeting.query
                                    .filter_by(date=form.add_meeting.data)
                                    .first())
            case.meeting_id = added_meeting.id
        case.consultant_id = form.consultant.data.id
        case.patient_id = patient_id
        case.next_opa = form.next_opa.data
        case.clinic_code = form.clinic_code.data
        case.planned_surgery = form.planned_surgery.data
        case.surgery_date = form.surgery_date.data
        case.medical_history = form.medical_history.data
        case.mdt_vcmg = form.mdt_vcmg.data
        case.question = form.question.data
        case.discussion = form.discussion.data
        flash(('Case updated for {f_name} {l_name}'
               ).format(f_name=patient.first_name,
                        l_name=patient.last_name))
        # add actions from form
        for act_field in action_list:
            form_action = form[act_field].data
            form_assigned_to = form[act_field + '_to'].data
            action_query = (Action.query
                                  .filter_by(case_id=case_id,
                                             form_field=act_field))
            action_row = action_query.first()
            if form_action and form_assigned_to:
                if action_row:
                    # form actions and row exist, update row
                    action_row.action = form_action
                    action_row.assigned_to_id = form_assigned_to.id
                    db.session.commit()
                else:
                    # form actions and no row, create row
                    new_action = Action(case_id=case_id,
                                        form_field=act_field,
                                        action=form_action,
                                        assigned_to=form_assigned_to)
                    db.session.add(new_action)
            elif action_row:
                # form field empty, but row exists, delete row
                to_remove = action_query.one()
                db.session.delete(to_remove)
        db.session.commit()
        case = Case.query.filter_by(id=case_id).first()
        return redirect(url_for('main.case_list'))
    return render_template('case_edit.html', cases=cases, form=form,
                           patient_id=patient_id, case_id=case_id,
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
    form = MeetingForm(obj=meeting)
    if form.validate_on_submit():
        meeting.date = form.date.data
        meeting.comment = form.comment.data
        meeting.is_cancelled = form.is_cancelled.data
        if form.is_cancelled.data:
            next_meeting = (Meeting.query
                                   .filter(Meeting.date > meeting.date,
                                           Meeting.is_cancelled == False)
                                   .order_by(Meeting.date)
                                   .first())
            if not next_meeting:
                flash('Cases could not be pushed to next meeting, '
                      'no meetings exist after this one')
            else:
                cases = Case.query.filter_by(meeting_id=pk)
                for case in cases:
                    if any(case.patient_id == next_meet_case.patient_id
                           for next_meet_case in next_meeting.cases):
                        flash(('Case for patient {f_name} {l_name} was not '
                               'moved as patient also has a case on {new_date}')
                              .format(f_name=case.patient.first_name,
                                      l_name=case.patient.last_name,
                                      old_date=meeting.date_repr,
                                      new_date=next_meeting.date_repr))
                    else:
                        case.meeting_id = next_meeting.id
                        flash(('Case for patient {f_name} {l_name} was moved '
                              'from {old_date} to {new_date}')
                              .format(f_name=case.patient.first_name,
                                      l_name=case.patient.last_name,
                                      old_date=meeting.date_repr,
                                      new_date=next_meeting.date_repr))
        db.session.commit()
        flash('Meeting for {date} has been edited'.format(date=form.date.data))
        return redirect(url_for('main.meeting_list'))
    return render_template('meeting_form.html', form=form, title='Edit meeting')


@main.route('/meetings')
@login_required
def meeting_list():
    """List all meetings"""
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
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
                          date_of_birth=form.date_of_birth.data,
                          sex=form.sex.data)
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
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        patient.hospital_number = form.hospital_number.data.strip()
        patient.first_name = form.first_name.data.strip()
        patient.last_name = form.last_name.data.strip()
        patient.date_of_birth = form.date_of_birth.data
        patient.sex = form.sex.data
        db.session.commit()
        flash('Patient edited'
              ' ({l_name}, {f_name})'.format(f_name=patient.first_name,
                                             l_name=patient.last_name.upper()))
        return redirect(url_for('main.patient_list'))
    return render_template('patient_form.html', form=form, title='Edit Patient')


@main.route('/patients')
@login_required
def patient_list():
    """List all meetings with newest first"""
    patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template('patient_list.html', patients=patients,
                           title='Patients')


@main.route('/actions/<user_id>/',  methods=['GET', 'POST'])
@main.route('/actions/',  methods=['GET', 'POST'])
@login_required
def action_list(user_id=None):
    """List all actions, filter by user_id if given.

    If action_id, complete action and check to see if all actions for case
    have been completed. If so, change the status
    """
    title = 'Actions '
    action_id = request.args.get('action_id')
    if action_id:
        # action_id to complete
        complete_action = Action.query.filter_by(id=action_id).first()
        complete_action.is_completed = True
        case = Case.query.filter_by(id=complete_action.case_id).first()
        case_actions = (Action.query
                              .filter_by(case_id=complete_action.case_id)
                              .all())
        if all(case_action.is_completed
               for case_action in case_actions):
            case.status = 'COMP'
        else:
            case.status = 'DISC'
        db.session.commit()
    if user_id:
        action_query = Action.query.filter_by(assigned_to_id=user_id)
        user = User.query.filter_by(id=user_id).first()
        title += 'for {username}'.format(username=user.username)
    else:
        action_query = Action.query
    actions = (action_query.order_by(Action.is_completed, Action.case_id.desc())
                           .all())
    return render_template('action_list.html', actions=actions, user_id=user_id,
                           title=title)


@main.route('/actions/edit/<int:action_id>/', methods=['GET', 'POST'])
@login_required
def action_edit(action_id):
    """Edit action entry"""
    user_id = request.args.get('user_id')
    action = Action.query.filter_by(id=action_id).first()
    form = ActionForm(obj=action)
    if form.validate_on_submit():
        action.action = form.action.data
        action.assigned_to_id = form.assigned_to.data.id
        action.is_completed = form.is_completed.data
        case = Case.query.filter_by(id=action.case_id).first()
        case_actions = Action.query.filter_by(case_id=action.case_id).all()
        if all(case_action.is_completed
               for case_action in case_actions):
            case.status = 'COMP'
        else:
            case.status = 'DISC'
        db.session.commit()
        flash('Action edited ({})'.format(action.action))
        return redirect(url_for('main.action_list', user_id=user_id))
    return render_template('action_form.html', form=form,
                           title='Edit Action')
