from flask import Flask, render_template

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from config import config

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
db = SQLAlchemy()
admin = Admin(template_mode='bootstrap3')

def create_app(config_name):
    global db
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    Bootstrap(app)
    db.init_app(app)
    login_manager.init_app(app)

    admin.init_app(app)
    admin.add_view(AdminModelView(User, db.session))
    admin.add_view(AdminModelView(Patient, db.session))
    admin.add_view(AdminModelView(Meeting, db.session))
    admin.add_view(AdminModelView(Case, db.session))
    admin.add_view(AdminModelView(Action, db.session))
    admin.add_view(AdminModelView(Attendee, db.session))

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app


class AdminModelView(ModelView):
    page_size = 50  # the number of entries to display on the list view

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return render_template('403.html')


# placed at end to avoid circular argument
from mdt_app.models import User, Case, Meeting, Action, Patient, Attendee
