from flask import Flask, render_template

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from flask_admin import Admin

from config import config
from mdt_app.admin.views import (AdminModelView, CustomAdminModelView,
                                 MyAdminIndexView)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
db = SQLAlchemy()


def create_app(config_name):
    global db
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    Bootstrap(app)
    db.init_app(app)
    login_manager.init_app(app)

    admin = Admin(template_mode='bootstrap3',
                  index_view=MyAdminIndexView())
    admin.init_app(app)
    admin.add_view(CustomAdminModelView(User, db.session))
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

# placed at end to avoid circular argument
from mdt_app.models import User, Case, Meeting, Action, Patient, Attendee
