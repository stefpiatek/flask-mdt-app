#!flask\Scripts\python.exe
import os

from flask_debugtoolbar import DebugToolbarExtension
from flask_script import Manager, Shell
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

from mdt_app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
toolbar = DebugToolbarExtension(app)
manager = Manager(app)
def make_shell_context():
    return dict(app=app, db=db)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)




if __name__ == '__main__':
    manager.run()
