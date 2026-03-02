from flask import Flask, jsonify, request, render_template, redirect, session, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
import json, requests, random, uuid, psutil, sys, os, string, yaml, hashlib, openpyxl
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from functools import wraps
from werkzeug.user_agent import UserAgent

with open('settings.yaml') as f:
	app_data = yaml.load(f, Loader=yaml.FullLoader)
f.close()

app = Flask(__name__)
bcrypt = Bcrypt(app)

db_host = app_data['db_host']
db_user = app_data['db_user']
db_name = app_data['db_name']
db_pass = app_data['db_pass']
default_phone = app_data['default_phone']
default_email = app_data['default_email']
default_pass = app_data['default_pass']
domain = app_data['domain']
default_subjects = app_data['default_subjects']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dja3a@2024$hul&vbyudju3i'
version = "0.1.1"

db = SQLAlchemy(app)

class Service(db.Model):
	__tablename__ = 'services'
	id = db.Column(db.Integer, primary_key = True)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	#subscriptions = relationship("Subscription", back_populates = "service")

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	#school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	#employee_id = db.Column(db.Integer, ForeignKey('employees.id'))
	uuid = db.Column(db.String)
	phone = db.Column(db.String, unique=True)
	code = db.Column(db.String)
	pwd = db.Column(db.String)
	rights = db.Column(db.String)
	deleted = db.Column(db.Boolean, default = False)
	#school = relationship("School", back_populates = "users")
	#employee = relationship("Employee", back_populates = "user")
	#logs = relationship("User_log", back_populates = "user")
	#devices = relationship("User_device", back_populates = "user")
	#shortcuts = relationship("Shortcut", back_populates = "user")

@app.route('/')
def home():
	session['version'] = version
	session['previous'] = "/"
	return render_template('home.html', records = {'title': "Application Test"})

@app.route('/login', methods = ['GET', 'POST'])
def login():
	phone = request.form['phone']
	password = request.form['password']
	user = User.query.filter_by(phone = phone).first()
	if user and user.pwd and bcrypt.check_password_hash(user.pwd, password):
		if user.rights == "Super Admin":
			session['super_admin'] = "Samis Admin"
			session['user'] = {'name': "Samis Admin", 'uuid': user.uuid}
			session['school'] = {'name': "Samis Systems Ltd"}
		else:
			school = user.school
			session['user'] = {'name': "Guest User", 'uuid': user.uuid, 'rights': user.rights}
			session['module'] = "Academics"
			if "Admin" in user.rights:
				session['admin'] = "Admin"
		flash("{} Logged in Successfully!".format(session['user']['name']), category = "success")
	else:
		flash("You entered incorect login details!", category = "danger")
	return redirect('/')

@app.route('/logout')
def logout():
	message = "{} was Logged Out Successfully".format(session['user']['name'])
	session.clear()
	flash(message, category = "success")
	return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port="6800", debug=False)