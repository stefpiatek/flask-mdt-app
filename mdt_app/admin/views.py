from flask import abort
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user


class AdminModelView(ModelView):
    """Model view, must be admin to access"""
    page_size = 50  # the number of entries to display on the list view

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class MyAdminIndexView(AdminIndexView):
    """Index view, must be admin to access"""
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class CustomAdminModelView(AdminModelView):
    """Custom list template to show unconfirmed users with a row in red"""
    list_template = 'admin/list.html'
