from flask import Blueprint

main = Blueprint('main', __name__)

# at end to avoid circular references
from . import views, errors
