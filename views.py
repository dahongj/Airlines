from flask import Blueprint, render_template, request, session, url_for, redirect

views = Blueprint('views',__name__)

@views.route('/')
def home():
    return render_template('home.html')