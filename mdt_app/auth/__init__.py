from flask import Blueprint

auth = Blueprint('auth', __name__)

# import at end to avoid circular reference
from . import views
