from datetime import date

from flask import render_template, redirect, request, url_for, flash, abort
from flask_login import login_required, current_user

from .. import db
from ..models import Case, Meeting, Patient, Action, Attendee, User
from . import main
from .forms import *


@main.route('/index')
def index():
    """Index page, link for users to change their own password"""
    return render_template('index.html', title='Welcome to the MDT App')


@main.route('/')
@main.route('/cases/',  methods=['GET', 'POST'])
@login_required
def case_list():
    """Returns cases, progress and attendee form

    Fairly bloated view but used for a lot of situations
    If meeting date request argument, generate attendee form and MDT progress
    otherwise set these to be null
    If push_cases, move undiscussed cases to next meeting
    For POST method, delete any attendees for meeting that are not in form
    add any new attendees.

    Request arguments:
    meeting -- date str: meeting date to filter by (e.g. 2017-09-20)
    push_cases -- if exists, push all undiscussed cases to next meeting


    Template variables:
    title -- title
    cases -- all cases (sorted by dec. meeting_date and inc. created_on)
    counts -- dictionary of total per status of cases, and percent complete
    attendee_form -- attendee form of all confirmed users
    attendees -- list of all attendee objects
    meeting -- meeting date
    """

    meeting_date = request.args.get('meeting')
    title = 'All cases'
    if meeting_date:
        meeting = Meeting.query.filter_by(date=meeting_date).first()
        case_query = Case.query.filter_by(meeting=meeting)
        attendees = Attendee.query.filter_by(meeting=meeting).all()
        attendee_list = [attendee.user for attendee in attendees]
        attendee_form = AttendeeForm(data={'user': attendee_list,
                                           'comment': meeting.comment})
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
                       .order_by(Meeting.date.desc(), Case.created_on)
                       .all())
    push_cases = request.args.get('push_cases')
    # Pick up submission from page
    if push_cases:
        # Push cases to next meeting
        next_meeting = (Meeting.query
                        .filter(Meeting.date > meeting_date,
                                Meeting.is_cancelled == False)
                        .order_by(Meeting.date)
                        .first())
        if not next_meeting:
            flash('Cases could not be pushed to next meeting, '
                  'no meetings exist after this one',
                  category='warning')
        else:
            for to_push in cases:
                if to_push.status == 'TBD':
                    if any(to_push.patient_id == next_meet_case.patient_id
                           for next_meet_case in next_meeting.cases):
                        flash(('Case for patient {f_name} {l_name} was not '
                               'moved as patient also has a case on {new_date}'
                               ).format(f_name=to_push.patient.first_name,
                                        l_name=to_push.patient.last_name,
                                        new_date=next_meeting.date_repr),
                              category='warning')
                    else:
                        to_push.meeting_id = next_meeting.id
                        flash(
                              ('Case for patient {f_name} {l_name} was moved '
                               'to {new_date}'
                               ).format(f_name=to_push.patient.first_name,
                                        l_name=to_push.patient.last_name,
                                        new_date=next_meeting.date_repr),
                              category='success')
            db.session.commit()
    elif request.method == 'POST' and attendee_form.validate_on_submit():
        # Case edit form
        meeting.comment = attendee_form.comment.data.strip()
        form_attendees = attendee_form.user.data
        for row_attendee in attendees:
            # remove users in database that are not in form data
            if not any(row_attendee.user.username == form_user.username
                       for form_user in form_attendees):
                db.session.delete(row_attendee)
        for form_user in form_attendees:
            # if form user not in database, add them
            if not any(form_user.username == row_attendee.user.username
                       for row_attendee in attendees):
                new_attendee = Attendee(meeting_id=meeting.id,
                                        user=form_user)
                db.session.add(new_attendee)
        db.session.commit()
        return redirect(url_for('main.case_list', meeting=meeting_date))
    return render_template('case_list.html', cases=cases, title=title,
                           counts=counts, attendee_form=attendee_form,
                           attendees=attendees, meeting=meeting_date)


@main.route('/cases/create/<patient_id>',  methods=['GET', 'POST'])
@login_required
def case_create(patient_id=None):
    """ Returns cases for patient and form to create new case for patient

    CaseCreateForm allows for selecting a meeting or entering one in manually
    Manually entered meeting date then creates this in the database.
    Strips leading and trailing whitespace from large text chunks


    Request arguments:
    patient_id -- int: patient_id to filter by

    Template variables:
    title -- title
    cases -- all cases (filtered by patient)
    form -- case_create form
    patient_id -- patient id
    """
    patient = Patient.query.filter_by(id=patient_id).first()
    cases = (Case.query
                 .filter_by(patient_id=patient_id)
                 .join(Meeting)
                 .order_by(Meeting.date.desc())
                 .all())
    title = ('Cases for {f_name} {l_name} {hosp}'
             ).format(f_name=patient.first_name,
                      l_name=patient.last_name,
                      hosp=patient.hospital_number)
    flash('Date of birth (age): {age}'.format(age=patient.date_of_birth_repr),
          category='post-header')
    # set case_id to be -1 so that validation methods won't match by case_id
    form = CaseForm(patient_id=patient_id, case_id=-1)
    if form.validate_on_submit():
        if form.meeting.data:
            meeting_id = form.meeting.data.id
        else:
            new_date = Meeting(date=form.add_meeting.data,
                               comment='')
            db.session.add(new_date)
            db.session.commit()
            flash('MDT meeting added for {}'.format(new_date.date_repr),
                  category='success')
            added_meeting = (Meeting.query
                                    .filter_by(date=form.add_meeting.data)
                                    .first())
            meeting_id = added_meeting.id
        case = Case(meeting_id=meeting_id,
                    consultant_id=form.consultant.data.id,
                    patient_id=patient_id,
                    next_opa=form.next_opa.data,
                    clinic_code=form.clinic_code.data,
                    planned_surgery=form.planned_surgery.data,
                    surgery_date=form.surgery_date.data,
                    medical_history=form.medical_history.data.strip(),
                    mdt_vcmg=form.mdt_vcmg.data,
                    question=form.question.data.strip(),
                    created_on=date.today(),
                    created_by_id=current_user.id,
                    status='TBD')
        db.session.add(case)
        db.session.commit()
        flash(('New case added for {f_name} {l_name}'
               ).format(f_name=patient.first_name,
                        l_name=patient.last_name),
              category='success')
        return redirect(url_for('main.case_list'))
    return render_template('case_create.html', cases=cases, form=form,
                           patient_id=patient_id,
                           title=title)


@main.route('/cases/edit/<patient_id>/<case_id>',  methods=['GET', 'POST'])
@login_required
def case_edit(patient_id=None, case_id=None):
    """ List cases for patient and case edit form

    CaseEditForm is an extended version of the CaseCreateForm that has
    fields for the MDT process.
    Strips leading and trailing whitespace from large text chunks

    Changes status of case as appropriate:
    - If no_actions in form is ticked, completes status
    - else if form doesn't have discussion filled, set to TBD (to be discussed)
    - else if form has new action - change to discussed

    When new action is added, saves and loads template scrolling down to
    the table position.

    Request arguments:
    patient_id -- int: patient id, required
    case_id --  int: case id, required

    Template variables:
    title -- str: title
    cases -- list: all case models for patient
    form -- form: CaseEditForm
    case -- model: current case being edited
    patient_id -- int: patient_id
    case_id -- int: case id
    """

    if not (patient_id and case_id):
        flash('Patient or case details not given', category='danger')
        return abort(404)
    patient = Patient.query.filter_by(id=patient_id).first()
    cases = (Case.query
                 .filter_by(patient_id=patient_id)
                 .join(Meeting)
                 .order_by(Meeting.date.desc())
                 .all())
    case = Case.query.filter_by(id=case_id).first()
    actions = (Action.query.filter_by(case_id=case_id)
                           .all())
    title = ('Cases for {f_name} {l_name} {hosp}'
             ).format(f_name=patient.first_name,
                      l_name=patient.last_name,
                      hosp=patient.hospital_number)
    flash('Date of birth (age): {age}'.format(age=patient.date_of_birth_repr),
          category='post-header')
    form = CaseEditForm(obj=case,
                        case_id=case_id)
    if request.method == 'GET':
        if case.status == 'COMP' and not actions:
            # Set up form, if case complete and no actions, tick no actions
            form.no_actions.data = True
    elif form.validate_on_submit():
        if form.no_actions.data:
            # No actions ticked, set to COMP
            case.status = 'COMP'
        elif not form.discussion.data:
            # No discussion, set to TBD
            case.status = 'TBD'
        elif form.action.data:
            # actions added, revert to DISC
            case.status = 'DISC'
        # save form data for cases
        if form.meeting.data:
            case.meeting_id = form.meeting.data.id
        else:
            new_date = Meeting(date=form.add_meeting.data,
                               comment='')
            db.session.add(new_date)
            db.session.commit()
            flash('MDT meeting added for {}'.format(new_date.date_repr),
                  category='success')
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
        case.medical_history = form.medical_history.data.strip()
        case.mdt_vcmg = form.mdt_vcmg.data
        case.question = form.question.data.strip()
        case.discussion = form.discussion.data.strip()
        flash(('Case updated for {f_name} {l_name}'
               ).format(f_name=patient.first_name,
                        l_name=patient.last_name),
              category='success')
        # add actions from form
        if form.action.data:
            new_action = Action(case_id=case_id,
                                action=form.action.data,
                                assigned_to=form.action_to.data)
            db.session.add(new_action)
        db.session.commit()
        case = Case.query.filter_by(id=case_id).first()
        if form.action.data:
            # reset action form to blank and load form at table
            form.action.data = None
            form.action_to.data = None
            return render_template('case_edit.html', cases=cases, form=form,
                                   case=case,
                                   patient_id=patient_id, case_id=case_id,
                                   scroll='discussion',
                                   title=title)
        return redirect(url_for('main.case_list'))
    return render_template('case_edit.html', cases=cases, form=form,
                           case=case,
                           patient_id=patient_id, case_id=case_id,
                           title=title)


@main.route('/meetings/create', methods=['GET', 'POST'])
@login_required
def meeting_create():
    """Create new meeting"""

    # set id to be -1 so that validation methods won't match by id
    form = MeetingForm(id=-1)
    if form.validate_on_submit():
        meeting = Meeting(date=form.date.data,
                          comment=form.comment.data,
                          is_cancelled=form.is_cancelled.data)
        db.session.add(meeting)
        db.session.commit()
        flash('New Meeting added for {date}'.format(date=form.date.data),
              category='success')
        return redirect(url_for('main.meeting_list'))
    return render_template('meeting_form.html', form=form,
                           title='Add a New Meeting')


@main.route('/meetings/edit/<int:pk>', methods=['GET', 'POST'])
@login_required
def meeting_edit(pk):
    """Edit meeting, if meeting is cancelled push cases to next meeting

    Do not move case if a meeting in the future that is no cancelled
    does not exist.
    Do not move case if the patient already has a case on that date.

    Request arguments:
    pk -- int: meeting id

    Template objects:
    title -- title
    form -- MeetingForm
    """

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
                      'no meetings exist after this one',
                      category='warning')
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
                                      new_date=next_meeting.date_repr),
                              category='warning')
                    else:
                        case.meeting_id = next_meeting.id
                        flash(('Case for patient {f_name} {l_name} was moved '
                              'from {old_date} to {new_date}')
                              .format(f_name=case.patient.first_name,
                                      l_name=case.patient.last_name,
                                      old_date=meeting.date_repr,
                                      new_date=next_meeting.date_repr),
                              category='success')
        db.session.commit()
        flash('Meeting for {date} has been edited'.format(date=form.date.data),
              category='success')
        return redirect(url_for('main.meeting_list'))
    return render_template('meeting_form.html', form=form, title='Edit meeting')


@main.route('/meetings')
@login_required
def meeting_list():
    """List all meetings by decreasing date"""

    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('meeting_list.html', meetings=meetings,
                           title='Meetings')


@main.route('/patients/create', methods=['GET', 'POST'])
@login_required
def patient_create():
    """Create new patient entry

    Whitespace stripped from text

    Template objects:
    title -- title
    form -- PatientForm
    """

    # set form id to -1 so the db entry id does not equal the form id
    form = PatientForm(id=-1)
    if form.validate_on_submit():
        # Remove whitespace from either side of string fields
        patient = Patient(hospital_number=(form.hospital_number.data.strip()
                                                                    .upper()),
                          first_name=form.first_name.data.strip().title(),
                          last_name=form.last_name.data.strip().upper(),
                          date_of_birth=form.date_of_birth.data,
                          sex=form.sex.data)
        db.session.add(patient)
        db.session.commit()
        flash('New Patient added'
              ' ({l_name}, {f_name})'.format(f_name=patient.first_name,
                                             l_name=patient.last_name),
              category='success')
        return redirect(url_for('main.patient_list'))
    return render_template('patient_form.html', form=form,
                           title='Add a New Patient')


@main.route('/patients/edit/<int:pk>', methods=['GET', 'POST'])
@login_required
def patient_edit(pk):
    """Edit patient entry

    Strips whitespace from text fields

    Request arguments:
    pk -- int: patient id

    Template objects:
    title -- title
    form -- PatientForm
    """

    patient = Patient.query.filter_by(id=pk).first()
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        patient.hospital_number = form.hospital_number.data.strip().upper()
        patient.first_name = form.first_name.data.strip().title()
        patient.last_name = form.last_name.data.strip().upper()
        patient.date_of_birth = form.date_of_birth.data
        patient.sex = form.sex.data
        db.session.commit()
        flash('Patient edited'
              ' ({l_name}, {f_name})'.format(f_name=patient.first_name,
                                             l_name=patient.last_name),
              category='success')
        return redirect(url_for('main.patient_list'))
    return render_template('patient_form.html', form=form, title='Edit Patient')


@main.route('/patients')
@login_required
def patient_list():
    """List all meetings with newest first

    Template objects:
    title
    patients -- list of all patients
    """

    patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template('patient_list.html', patients=patients,
                           title='Patients')


@main.route('/actions/<user_id>/',  methods=['GET', 'POST'])
@main.route('/actions/',  methods=['GET', 'POST'])
@login_required
def action_list(user_id=None):
    """List all actions, filter by user_id if given.

    If user_id is given, filter by the user. If not return all actions.

    Complete action directly from list using action_id request argument.
    If all actions in case are complete, update the case status to be COMP
    otherwise set status of case as DISC.

    Request arguments:
    user_id -- int: user id to filter by if given.
    action_id -- int: id of action that is completed, update db accordingly

    Template objects:
    title -- title
    user_id -- int: user id for actions
    actions -- list: action models for user
    """
    title = 'Actions '
    if user_id:
        action_query = Action.query.filter_by(assigned_to_id=user_id)
        user = User.query.filter_by(id=user_id).first()
        title += 'assigned to {} {}'.format(user.f_name, user.l_name)
    else:
        action_query = Action.query
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
    actions = (action_query.join(Case)
                           .order_by(Action.is_completed,
                                     Case.status.desc(),
                                     Action.id.desc())
                           .all())
    return render_template('action_list.html', actions=actions, user_id=user_id,
                           title=title)


@main.route('/actions/edit/<int:action_id>/', methods=['GET', 'POST'])
@login_required
def action_edit(action_id):
    """Edit action entry

    Query case, if all actions complete, set case status to COMP
    otherwise set case status to DISC.

    Request arguments:
    action_id -- int: id of action to be edited

    Template objects:
    title
    form = ActionForm
    """
    user_id = request.args.get('user_id')
    action = Action.query.filter_by(id=action_id).first()
    delete_action = request.args.get('delete_action')
    if delete_action:
        case_id = action.case_id
        db.session.delete(action)
        db.session.commit()
        flash("Action '{act}' deleted".format(act=action.action),
              category='success')
        remaining_actions = Action.query.filter_by(case_id=case_id).all()
        if not remaining_actions:
            case = Case.query.filter_by(id=case_id).first()
            case.status = 'TBD'
            db.session.commit()
            flash("Case status is now 'to be discussed' "
                  "because all actions have been removed",
                  category='info')
        return redirect(url_for('main.action_list', user_id=user_id))

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
        flash('Action edited ({})'.format(action.action),
              category='success')
        return redirect(url_for('main.action_list', user_id=user_id))
    return render_template('action_form.html', form=form,
                           title='Edit Action', action=action)
