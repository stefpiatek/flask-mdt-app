# Design rationale

This document will cover what choices were made and options that were explored during the development of the MDT app.

## Current issues that are not addressed at this stage

- Issue 5.
  - Access to patient demographics database is not likely to be granted without incurring substantial time and cost.

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
- Pytest was chosen for it's limited boiler plate
- Custom CSS and scripts are in the base.html file, aiming to have few custom styles and scripts
- Datatables used for pretty tables and to allow for sorting by the user
