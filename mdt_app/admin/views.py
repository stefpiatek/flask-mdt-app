from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user


class AdminModelView(ModelView):
    page_size = 50  # the number of entries to display on the list view

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return render_template('403.html')


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return render_template('403.html')


class CustomAdminModelView(AdminModelView):
    list_template = 'admin/list.html'
