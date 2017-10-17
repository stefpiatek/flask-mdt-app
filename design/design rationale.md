# Design rationale

This document will cover what choices were made and options that were explored during the development of the MDT app.

## Current issues that are not addressed at this stage

- Issue 5.
  - Access to patient demographics database is not likely to be granted without incurring substantial time and cost.

## To do list:

- Unit tests to increase coverage
- Audit log tables for all changes in cases, actions and attendees
- Export case report to document (e.g. pdf)
- Field for PA has added action to patient record
- Email notification of being assigned an action, perhaps reminders
- Email notification for admins that new user has registered
- Perhaps change is_confirmed column to be called is_active in users table, consistent with flask_login defaults  

  
## Solution types considered

Access database

- Would require trust computers in MDT meeting to have MS Access to be installed
- Design of pleasing user interface is time consuming
- Lack of extensibility for other uses, or integrating within a web application. 

Django web application

- Accessible from any trust location, with user authentication. 
- Currently not used in development within the department and therefore providing support would be difficult. 
- Extensibility is possible, though difficult for non-SQL queries. 

Flask web application

- Accessible from any trust location, with user authentication. 
- Flask framework is used within the department and therefore providing ongoing support and development is possible. 
- Flexible extensibility.


## Implementation

- Flask web application would meet the majority of the requirements. 
    - No extra software installation by users.
    - Support can be offered by the department.
- The project is carried out iteratively in using a waterfall model


## Python modules, flask extensions, CSS and javascript

- Alembic, SQLalchemy and wtforms were chosen as they appear to be the standard for flask applications
- Flask-Admin gives quick access to an admin page, had already set up user authentication so only the admin page aspect used
- Flask-bootstrap made the project more lightweight as no bootstrap code was requried
- Flask-Script made command line interaction easier for migrations running of the server and loading a console within the flask app
- Pytest was chosen for it's limited boiler plate testing
- Custom CSS and scripts are in the base.html file, so that all custom functions and classes are obvious
- Datatables used for pretty tables, to allow for sorting by the user and searching the tables
- bootstrap-datapicker used as a datepicker was requested.
    - First used jQuery-ui's datepicker and then later found a bootstrap datepicker
	- Bootstrap-datepicker was chosen as it fits with the aesthetics and doesn't involve importing a whole UI module for one function

