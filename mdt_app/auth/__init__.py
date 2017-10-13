"""
Auth module is for user registration, login and changing login details
"""

from flask import Blueprint

auth = Blueprint('auth', __name__)

# import at end to avoid circular reference
from . import views
