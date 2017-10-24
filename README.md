# Flask MDT App

Flask app for project in Clinical Computing rotation of STP. 

## Status

This was developed as a project for a rotation and is a functional flask app. 
The design folder contains a list of extra features and requirements,
but I have since left the department and they have continued development. 

## MDT app overview

This projects uses the flask microframework and this section gives a quick rundown of what 
each part of the app is used for. For each module, the __init__ file gives a quick description
of the module's purpose and function. 

- config.py - stores settings for testing, development and production.
    - Default is development but os environment variable FLASK_CONFIG
      sets the configuration
- manage.py can be for command line
    - python manage.py runserver - run server
    - python manage.py db - run alembic commands
    - python shell - run command line python with the mdt_app
- secret_info.py - all information that should be no loaded into a public repo
- design folder contains some basic requirement and design choices information
- migrations folder - alembic migrations of database
- tests folder contains all tests (pytest)
- venv folder may be present, contains python virtual environment
- mdt_app module (this module)
    - Contains modules for different bluebrints (admin, auth and main)
    - static folder contains all javascript and css
    - templates folder contains all Jinja2 templates for site
    - models.py - data models
    - decorators.py - decorator for admin_required for access to view
    
