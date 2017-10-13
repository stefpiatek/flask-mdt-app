"""
Main module is for all other views, forms and errors for the app that are not
administration of tables or user logins
"""
from flask import Blueprint

main = Blueprint('main', __name__)

# at end to avoid circular references
from . import views, errors
