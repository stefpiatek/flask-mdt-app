from functools import wraps

from flask import abort

from flask_login import current_user

def admin_required(func):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if current_user.is_admin is False:
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator(func)
