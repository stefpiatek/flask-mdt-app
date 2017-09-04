from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from config import config

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
db = SQLAlchemy()
mail = Mail()
admin = Admin(template_mode = 'bootstrap3')

def create_app(config_name):
    # create bootstrap templates
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    Bootstrap(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    admin.init_app(app)
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Patient, db.session))
    admin.add_view(ModelView(Meeting, db.session))
    admin.add_view(ModelView(Case, db.session))
    admin.add_view(ModelView(Action, db.session))



    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

# placed at end to avoid circular argument
from mdt_app.models import User, Case, Meeting, Action, Patient
