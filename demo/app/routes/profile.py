from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import Database
from werkzeug.security import generate_password_hash ,check_password_hash
from functools import wraps

profile = Blueprint('profile', __name__)
database = Database()

@profile.route('/profile_edit')
def edit():
    return render_template('profile_edit.html')