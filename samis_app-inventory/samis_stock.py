from flask import Flask, jsonify, request, render_template, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
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
scheduler = BackgroundScheduler()

db_host = app_data['db_host']
db_user = app_data['db_user']
db_name = app_data['db_name']
db_pass = app_data['db_pass']
email_key = app_data['email_key']
sender_email = app_data['sender_email']
sms_key = app_data['sms_key']
sms_pid = app_data['sms_pid']
sender_id = app_data['sender_id']
default_phone = app_data['default_phone']
default_email = app_data['default_email']
default_pass = app_data['default_pass']
domain = app_data['domain']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data_stock.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{}:{}@{}/{}'.format(db_user, db_pass, db_host, db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '$@m!$@2024$hul&vbyudju3i'
bcrypt = Bcrypt(app)
version = "0.1.17"

db = SQLAlchemy(app)

class Service(db.Model):
	__tablename__ = 'services'
	id = db.Column(db.Integer, primary_key = True)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	subscriptions = relationship("Subscription", back_populates = "service")

class School(db.Model):
	__tablename__= 'schools'
	id = db.Column(db.Integer, primary_key = True)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	phone = db.Column(db.String)
	address = db.Column(db.String)
	motto = db.Column(db.String)
	logo = db.Column(db.String, default = "blank.jpeg")
	#last_po = db.Column(db.Integer, default = 0)
	#last_rq = db.Column(db.Integer, default = 0)
	status = db.Column(db.String, default = "Active")
	config = relationship("School_configuration", uselist=False, back_populates = "school")
	users = relationship("User", back_populates = "school")
	departments = relationship("Department", back_populates = "school")
	stores = relationship("Store", back_populates = "school")
	products = relationship("Product", back_populates = "school")
	orders = relationship("Purchase_order", back_populates = "school")
	requests = relationship("Request_quantity", back_populates = "school")
	suppliers = relationship("Supplier", back_populates = "school")
	units = relationship("Unit", back_populates = "school")
	deleted_items = relationship("Deleted_item", back_populates = "school")
	user_logs = relationship("User_log", back_populates = "school")
	subscriptions = relationship("Subscription", back_populates = "school")
	changes = relationship("Samis_Activity", back_populates = "school")

class School_configuration(db.Model):
	__tablename__ = 'school_configurations'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	last_po = db.Column(db.Integer, default = 0)
	last_rq = db.Column(db.Integer, default = 0)
	school = relationship("School", back_populates = "config")

class Subscription(db.Model):
	__tablename__ = 'subscriptions'
	id = db.Column(db.Integer, primary_key = True)
	service_id = db.Column(db.Integer, ForeignKey('services.id'))
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	date = db.Column(db.String)
	balance = db.Column(db.Float, default = 0)
	status = db.Column(db.String, default = "Active")
	service = relationship("Service", back_populates = "subscriptions")
	school = relationship("School", back_populates = "subscriptions")

class Samis_Activity(db.Model):
	__tablename__= 'samis_activities'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	change = db.Column(db.String)
	remarks = db.Column(db.String)
	date = db.Column(db.String)
	school = relationship("School", back_populates = "changes")

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	employee_id = db.Column(db.Integer, ForeignKey('employees.id'))
	uuid = db.Column(db.String)
	phone = db.Column(db.String, unique=True)
	code = db.Column(db.String)
	pwd = db.Column(db.String)
	rights = db.Column(db.String)
	deleted = db.Column(db.Boolean, default = False)
	school = relationship("School", back_populates = "users")
	employee = relationship("Employee", back_populates = "user")
	logs = relationship("User_log", back_populates = "user")
	shortcuts = relationship("Shortcut", back_populates = "user")
	devices = relationship("User_device", back_populates = "user")
	purchase_orders = relationship("Purchase_order", back_populates = "manager")
	requests = relationship("Request_quantity", back_populates = "manager")

class User_device(db.Model):
	__tablename__= 'user_devices'
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	#uuid = db.Column(db.String)
	name = db.Column(db.String)
	data = db.Column(db.String)
	status = db.Column(db.String, default = "New")
	user = relationship("User", back_populates = "devices")

class User_log(db.Model):
	__tablename__= 'user_logs'
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	resource = db.Column(db.String)
	action = db.Column(db.String)
	address = db.Column(db.String)
	time = db.Column(db.String)
	school = relationship("School", back_populates = "user_logs")
	user = relationship("User", back_populates = "logs")

class Deleted_item(db.Model):
	__tablename__ = 'deleted_items'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	category = db.Column(db.String)
	name = db.Column(db.String)
	uuid = db.Column(db.String)
	item_id = db.Column(db.Integer)
	status = db.Column(db.String, default = "Removed")
	date = db.Column(db.String)
	school = relationship("School", back_populates = "deleted_items")

class Search(db.Model):
	__tablename__ = 'search'
	id = db.Column(db.Integer, primary_key = True)
	category = db.Column(db.String)
	name = db.Column(db.String)
	uuid = db.Column(db.String)
	terms = db.Column(db.String)
	icon = db.Column(db.String)
	image = db.Column(db.String)
	date = db.Column(db.String)

class Shortcut(db.Model):
	__tablename__ = 'shortcuts'
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	link = db.Column(db.String)
	icon = db.Column(db.String)
	status = db.Column(db.String, default = "Active")
	user = relationship("User", back_populates = "shortcuts")

class Log(db.Model):
	__tablename__= 'logs'
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.String)
	resource = db.Column(db.String)
	action = db.Column(db.String)
	address = db.Column(db.String)
	time = db.Column(db.String)

class Unit(db.Model):
	__tablename__ = 'units'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	one = db.Column(db.String)
	category = db.Column(db.String, default = "Standard")
	sub_unit = db.Column(db.String)
	sub_value = db.Column(db.Float)
	deleted = db.Column(db.Boolean, default = False)
	school = relationship("School", back_populates = "units")
	products = relationship("Product", back_populates = "unit")

class All_product(db.Model):
	__tablename__ = 'all_products'
	id = db.Column(db.Integer, primary_key = True)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	category = db.Column(db.String, default = "s1")
	image = db.Column(db.String, default = "blank.png")

class Product(db.Model):
	__tablename__ = 'products'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	unit_id = db.Column(db.Integer, ForeignKey('units.id'), default = 1)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	category = db.Column(db.String, default = "s1")
	image = db.Column(db.String, default = "blank.png")
	reorder_level = db.Column(db.Float, default = 0)
	reorder_quantity = db.Column(db.Float, default = 0)
	cost = db.Column(db.Float, default = 0)
	quantity = db.Column(db.Float, default = 0)
	deleted = db.Column(db.Boolean, default = False)
	#requested = db.Column(db.Integer, default = 0)
	school = relationship("School", back_populates = "products")
	unit = relationship("Unit", back_populates = "products")
	stock = relationship("Stock", back_populates = "product")
	assets = relationship("Asset", back_populates = "product")
	order_items = relationship("Order_item", back_populates = "product")
	stock_logs = relationship("Stock_log", back_populates = "product")

class Stock_log(db.Model):
	__tablename__ = 'stock_logs'
	id = db.Column(db.Integer, primary_key = True)
	product_id = db.Column(db.Integer, ForeignKey('products.id'))
	uuid = db.Column(db.String)
	details = db.Column(db.String)
	quantity = db.Column(db.Float, default = 0)
	balance = db.Column(db.Float, default = 0)
	date = db.Column(db.String)
	product = relationship("Product", back_populates = "stock_logs")

class Purchase_order(db.Model):
	__tablename__ = 'purchase_orders'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	supplier_id = db.Column(db.Integer, ForeignKey('suppliers.id'))
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	uuid = db.Column(db.String)
	category = db.Column(db.String)
	date = db.Column(db.String)
	value = db.Column(db.Float, default = 0)
	no = db.Column(db.Integer, default = 0)
	status = db.Column(db.String, default = "draft")
	school = relationship("School", back_populates = "orders")
	supplier = relationship("Supplier", back_populates = "purchase_orders")
	manager = relationship("User", back_populates = "purchase_orders")
	order_items = relationship("Order_item", back_populates = "purchase_order")

class Order_item(db.Model):
	__tablename__ = 'order_items'
	id = db.Column(db.Integer, primary_key = True)
	product_id = db.Column(db.Integer, ForeignKey('products.id'))
	purchase_order_id = db.Column(db.Integer, ForeignKey('purchase_orders.id'))
	stock_id = db.Column(db.Integer, ForeignKey('stock.id'))
	uuid = db.Column(db.String)
	specification = db.Column(db.String)
	quantity = db.Column(db.Integer)
	returned = db.Column(db.Float, default = 0)
	price = db.Column(db.Float, default = 0)
	product = relationship("Product", back_populates = "order_items")
	purchase_order = relationship("Purchase_order", back_populates = "order_items")
	stock = relationship("Stock", back_populates = "order_items")
	assets = relationship("Asset", back_populates = "order_item")
	returns = relationship("Outward", back_populates = "order_item")

class Asset(db.Model):
	__tablename__ = 'assets'
	id = db.Column(db.Integer, primary_key = True)
	product_id = db.Column(db.Integer, ForeignKey('products.id'))
	order_item_id = db.Column(db.Integer, ForeignKey('order_items.id'))
	owner_id = db.Column(db.Integer, ForeignKey('employees.id'))
	department_id = db.Column(db.Integer, ForeignKey('departments.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	acquired_on = db.Column(db.String)
	tag = db.Column(db.String)
	location = db.Column(db.String)
	serial = db.Column(db.String, unique=True)
	description = db.Column(db.String)
	depreciation = db.Column(db.Float, default = 0)
	service = db.Column(db.Integer, default = 0)
	waranty = db.Column(db.Integer, default = 0)
	price = db.Column(db.Float)
	value = db.Column(db.Float)
	status = db.Column(db.String, default = "New")
	deleted = db.Column(db.Boolean, default = False)
	age = db.Column(db.Integer, default = 0)
	product = relationship("Product", back_populates = "assets")
	order_item = relationship("Order_item", back_populates = "assets")
	owner = relationship("Employee", back_populates = "assets")
	department = relationship("Department", back_populates = "assets")
	depreciations = relationship("Depreciation", back_populates = "asset")
	maintenances = relationship("Maintenance", back_populates = "asset")
	activities = relationship("Asset_activity", back_populates = "asset")

class Asset_activity(db.Model):
	__tablename__ = 'asset_activities'
	id = db.Column(db.Integer, primary_key = True)
	asset_id = db.Column(db.Integer, ForeignKey('assets.id'))
	uuid = db.Column(db.String)
	details = db.Column(db.String)
	remarks = db.Column(db.String)
	date = db.Column(db.String)
	asset = relationship("Asset", back_populates = "activities")

class Depreciation(db.Model):
	__tablename__ = 'depreciations'
	id = db.Column(db.Integer, primary_key = True)
	asset_id = db.Column(db.Integer, ForeignKey('assets.id'))
	uuid = db.Column(db.String)
	details = db.Column(db.String)
	amount = db.Column(db.Float)
	date = db.Column(db.String)
	asset = relationship("Asset", back_populates = "depreciations")

class Maintenance(db.Model):
	__tablename__ = 'maintenances'
	id = db.Column(db.Integer, primary_key = True)
	asset_id = db.Column(db.Integer, ForeignKey('assets.id'))
	uuid = db.Column(db.String)
	details = db.Column(db.String)
	date = db.Column(db.String)
	next_service = db.Column(db.String)
	asset = relationship("Asset", back_populates = "maintenances")

class Employee(db.Model):
	__tablename__ = 'employees'
	id = db.Column(db.Integer, primary_key = True)
	department_id = db.Column(db.Integer, ForeignKey('departments.id'), default = 1)
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	#staff_id = db.Column(db.String)
	#tsc_no = db.Column(db.String)
	phone = db.Column(db.String)
	category = db.Column(db.String)
	designation = db.Column(db.String)
	location = db.Column(db.String)
	#image = db.Column(db.String, default = "samis.jpg")
	deleted = db.Column(db.Boolean, default = False)
	department = relationship("Department", back_populates = "employees")
	stores = relationship("Store", back_populates = "manager")
	assets = relationship("Asset", back_populates = "owner")
	user = relationship("User", back_populates = "employee", uselist=False)
	activities = relationship("Employee_activity", back_populates = "employee")

class Employee_activity(db.Model):
	__tablename__ = 'employee_activities'
	id = db.Column(db.Integer, primary_key = True)
	employee_id = db.Column(db.Integer, ForeignKey('employees.id'))
	uuid = db.Column(db.String)
	date = db.Column(db.String)
	name = db.Column(db.String)
	employee = relationship("Employee", back_populates = "activities")

class Supplier(db.Model):
	__tablename__ = 'suppliers'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	phone = db.Column(db.String)
	address = db.Column(db.String)
	deleted = db.Column(db.Boolean, default = False)
	school = relationship("School", back_populates = "suppliers")
	purchase_orders = relationship("Purchase_order", back_populates = "supplier")

class Department(db.Model):
	__tablename__ = 'departments'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	description = db.Column(db.String)
	status = db.Column(db.String)
	deleted = db.Column(db.Boolean, default = False)
	school = relationship("School", back_populates = "departments")
	employees = relationship("Employee", back_populates = "department")
	assets = relationship("Asset", back_populates = "department")
	requests = relationship("Request_quantity", back_populates = "department")

class Store(db.Model):
	__tablename__ = 'stores'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	manager_id = db.Column(db.Integer, ForeignKey('employees.id'))
	uuid = db.Column(db.String)
	name = db.Column(db.String)
	location = db.Column(db.String)
	deleted = db.Column(db.Boolean, default = False)
	manager = relationship("Employee", back_populates = "stores")
	stock = relationship("Stock", back_populates = "store")
	school = relationship("School", back_populates = "stores")

class Request_quantity(db.Model):
	__tablename__ = 'request_quantities'
	id = db.Column(db.Integer, primary_key = True)
	school_id = db.Column(db.Integer, ForeignKey('schools.id'))
	department_id = db.Column(db.Integer, ForeignKey('departments.id'))
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	uuid = db.Column(db.String)
	date = db.Column(db.String)
	no = db.Column(db.Integer, default = 0)
	status = db.Column(db.String, default = "draft")
	bg_color = db.Column(db.String, default = "primary")
	school = relationship("School", back_populates = "requests")
	department = relationship("Department", back_populates = "requests")
	manager = relationship("User", back_populates = "requests")
	rq_items = relationship("RQ_item", back_populates = "request")

class Stock(db.Model):
	__tablename__ = 'stock'
	id = db.Column(db.Integer, primary_key = True)
	product_id = db.Column(db.Integer, ForeignKey('products.id'))
	store_id = db.Column(db.Integer, ForeignKey('stores.id'))
	uuid = db.Column(db.String)
	quantity = db.Column(db.Float, default = 0)
	product = relationship("Product", back_populates = "stock")
	store = relationship("Store", back_populates = "stock")
	order_items = relationship("Order_item", back_populates = "stock")
	rq_items = relationship("RQ_item", back_populates = "stock")

class RQ_item(db.Model):
	__tablename__ = 'rq_items'
	id = db.Column(db.Integer, primary_key = True)
	request_quantity_id = db.Column(db.Integer, ForeignKey('request_quantities.id'))
	stock_id = db.Column(db.Integer, ForeignKey('stock.id'))
	uuid = db.Column(db.String)
	specification = db.Column(db.String)
	quantity = db.Column(db.Float, default = 0)
	returned = db.Column(db.Float, default = 0)
	assets = db.Column(db.Integer, default = 0)
	request = relationship("Request_quantity", back_populates = "rq_items")
	stock = relationship("Stock", back_populates = "rq_items")
	returns = relationship("Inward", back_populates = "rq_item")

class Inward(db.Model):
	__tablename__ = 'inwards'
	id = db.Column(db.Integer, primary_key = True)
	rq_item_id = db.Column(db.Integer, ForeignKey('rq_items.id'))
	uuid = db.Column(db.String)
	quantity = db.Column(db.Float)
	date = db.Column(db.String)
	rq_item = relationship("RQ_item", back_populates = "returns")

class Outward(db.Model):
	__tablename__ = 'outwards'
	id = db.Column(db.Integer, primary_key = True)
	order_item_id = db.Column(db.Integer, ForeignKey('order_items.id'))
	uuid = db.Column(db.String)
	quantity = db.Column(db.Float)
	date = db.Column(db.String)
	order_item = relationship("Order_item", back_populates = "returns")

@app.errorhandler(Exception)
def internal_error(error):
	get_log("error", request.path)
	flash("Critical Error. Please contact the System Administrator!", category = "danger")
	#return redirect('/')
	return render_template('error.html', records = {'title': "error", 'data': "Please contact the administrator!"})

def verify_session(fn):
	@wraps(fn)
	def inner(*args,**kwargs):
		if 'user' not in session:
			session['version'] = version
			return render_template('login.html')
		return fn(*args,**kwargs)
	return inner

def verify_admin(fn):
	@wraps(fn)
	def inner(*args,**kwargs):
		if 'admin' not in session:
			return redirect('/')
		return fn(*args,**kwargs)
	return inner

def verify_super_admin(fn):
	@wraps(fn)
	def inner(*args,**kwargs):
		if 'super_admin' not in session:
			return redirect('/')
		return fn(*args,**kwargs)
	return inner

def verify_school_status(fn):
	@wraps(fn)
	def inner(*args,**kwargs):
		if session['school']['status'] != "Active":
			flash("The School: {} is Suspended.".format(session['school']['name']), category = "danger")
			flash("Please contact the administrator for details!", category = "danger")
			return redirect('/')
		return fn(*args,**kwargs)
	return inner

def update_session(user):
	session['filter'] = "all"
	if user.rights == "Super Admin":
		session['super_admin'] = "Samis Admin"
		session['user'] = {'name': "Samis Admin", 'uuid': user.uuid}
		session['school'] = {'name': "Samis Systems Ltd"}
	else:
		school = user.school
		session['user'] = {'name': user.employee.name, 'uuid': user.uuid, 'rights': user.rights}
		session['samis'] = school.id
		session['school'] = {'name': school.name, 'logo': school.logo, 'uuid': school.uuid, 'status': school.status}
		session['module'] = "Inventory"
		if "Admin" in user.rights:
			session['admin'] = "Admin"

def get_log(page, data, user=None):
	if not user:
		user = session['user']['name'] if ('user' in session) else "Guest Tester"
		address = request.access_route[-1]
	else:
		address = domain
	if data != "/favicon.ico":
		log = Log(user = user, resource = page, action = data, address = address, time = get_time("time"))
		db.session.add(log)
		db.session.commit()

def log_activity(action, data):
	address = request.access_route[-1]
	if 'samis' in session:
		school_id = int(session['samis'])
		user = User.query.filter_by(uuid = session['user']['uuid']).first()
		log = User_log(user_id = user.id, school_id = school_id, resource = action, action = data, address = address, time = get_time("time"))
		db.session.add(log)
	db.session.commit()

def send_text(phone, text, user):
	print(text)
	flash(text, category = "success")
	'''host = request.host_url
	if "@" in phone:
		topic = "Message from {}".format(user)
		body = "<h3>{}</h3><p>{}</p><i>Regards,<br>{}<br>{}</i>".format(topic, text, user, host)
		message = Mail(from_email = sender_email, to_emails = phone, subject = topic, html_content = body)
		sg = SendGridAPIClient(email_key)
		response = sg.send(message)
	else:
		if len(phone) == 10:
			phone = "254" + phone[1:]
		elif phone[0] == "+":
			phone = phone[1:]
		api_url = "https://sms.textsms.co.ke/api/services/sendsms/?"
		r = requests.get("{}apikey={}&partnerID={}&message={}&shortcode={}&mobile={}".format(api_url, sms_key, sms_pid, text, sender_id, phone))'''
	get_log("send message", phone)

def get_school_data(data_type):
	school = get_school()
	#school_id = int(session['samis'])
	#school = db.session.get(School, school_id)
	data_list = []
	if data_type == "employees":
		for department in school.departments:
			for employee in department.employees:
				if not employee.deleted:
					data_list.append(employee)
	elif data_type == "stock":
		for product in school.products:
			for stock in product.stock:
				data_list.append(stock)
	elif data_type == "assets":
		for product in school.products:
			for asset in product.assets:
				data_list.append(asset)
	elif data_type == "po_items":
		for order in school.orders:
			for item in order.order_items:
				data_list.append(item)
	elif data_type == "rq_items":
		for request in school.requests:
			for item in request.rq_items:
				data_list.append(item)
	elif data_type == "outwards":
		for order in school.orders:
			for order_item in order.order_items:
				for item in order_item.returns:
					data_list.append(item)
	elif data_type == "inwards":
		for request in school.requests:
			for rq_item in request.rq_items:
				for item in rq_item.returns:
					data_list.append(item)
	return data_list

def get_stock(product_id, store_id):
	stock = Stock.query.filter_by(product_id = product_id, store_id = store_id).first()
	if not stock:
		stock = Stock(uuid = uuid.uuid1().hex, product_id = product_id, store_id = store_id)
		db.session.add(stock)
		db.session.commit()
		db.session.refresh(stock)
	return stock

def check_availability(stock, quantity):
	quantity = stock.quantity - quantity
	return False if quantity < 0 else True

def update_order(order):
	value = 0
	for item in order.order_items:
		value = value + item.price * item.quantity
	order.value = value
	db.session.commit()

def get_time(category):
	if category == "date":
		return datetime.now().strftime("%d %B, %Y")
	elif category == "time":
		return datetime.now().strftime("%H:%M:%S %d %B, %Y")
	elif category == "year":
		return datetime.now().strftime("%Y")

@app.route('/')
@verify_session
def home():
	get_log("home", "view")
	session['previous'] = "/"
	if session['user']['name'] == "Samis Admin":
		data = {'schools': School.query.all(), 'users': User.query.all(), 'modules': Service.query.all()}
		return render_template('samis_admin/boards.html', records = data)
	else:
		school_id = int(session['samis'])
		#school = db.session.get(School, school_id)
		school = get_school()
		suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
		departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
		employees = get_school_data("employees")
		stores = [ store for store in school.stores if store.deleted == False]
		suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
		user = User.query.filter_by(uuid = session['user']['uuid']).first()
		shortcuts = user.shortcuts
		rq_items = [ item for item in get_school_data("rq_items") if item.assets > 0]
		products = [product for product in school.products if product.reorder_level > product.quantity]
		unreleased_items = len(rq_items)
		reorder_items = len(products)
		units = Unit.query.filter_by(deleted = False, school_id = school_id).all()
		data = {'suppliers': suppliers, 'departments': departments, 'stores': stores, 'suppliers': suppliers, 'employees': employees, 'shortcuts': shortcuts, 'units': units, 'unreleased_items': unreleased_items, 'reorder_items': reorder_items}
		return render_template('inventory/boards.html', records = data)

@app.route('/search/<text>')
@verify_session
def search(text):
	tags = "%{}%".format(text)
	result = Search.query.filter(Search.terms.ilike(tags)).all()
	results = {'query': text, 'list': result}
	get_log("search", text)
	return render_template('/search.html', results = results)

@app.route('/login', methods = ['GET', 'POST'])
def login():
	phone = request.form['phone']
	password = request.form['password']
	user = User.query.filter_by(phone = phone).first()
	if user and user.pwd and bcrypt.check_password_hash(user.pwd, password):
		device = get_user_device(user, request.user_agent)
		if device.status == "Active" or user.rights == "Super Admin":
			update_session(user)
			flash("Hello {}. Welcome to Samis App".format(session['user']['name']), category = "success")
			return redirect('/')
		else:
			flash("New device detected! An OTP was sent to verify!", "danger")
			user.code = random.randint(100000, 999999)
			db.session.commit()
			text = "Use the code {} to add new device.".format(user.code)
			send_text(phone, text, "SAMIS Admin")
			return redirect('/add_device')
	else:
		get_log("login failed", phone)
		flash("You entered incorect login details!", category = "danger")
		return redirect('/')

@app.route('/logout')
@verify_session
def logout():
	get_log("logout", "Success")
	#log_activity("Logged Out", "Successfully")
	message = "{} was Logged Out Successfully".format(session['user']['name'])
	session.clear()
	flash(message, category = "success")
	return redirect('/')

@app.route('/reset_pass/<ids>', methods = ['GET', 'POST'])
def reset_pass(ids):
	user = None
	if ids == "send":
		phone = request.form['phone']
		user = User.query.filter_by(phone = phone).first()
		for item in User.query.filter(User.code != None).all():
			item.code = None
		if user:
			user.code = random.randint(100000, 999999)
			db.session.commit()
			session['sent'] = "YES"
			text = "Use the code {} to reset your password.".format(user.code)
			send_text(phone, text, "SAMIS Admin")
			flash("A code was sent to {}".format(phone), category = "success")
			user = "code"
	elif "samis" in ids:
		code = ids.replace("samis", "")
		user = User.query.filter_by(code = code).first()
		flash("Welcome {}".format(user.employee.name), category = "success")
	elif ids == "verify":
		code = request.form['code']
		user = User.query.filter_by(code = code).first()
		if user:
			flash("Welcome {}".format(user.employee.name), category = "success")
		else:
			flash("The code entered is incorrect!", category = "danger")
			user = "code"
	elif ids == "change":
		pwd = request.form['pwd']
		user_id = request.form['user_id']
		user = db.session.get(User, user_id)
		user.code = None
		user.pwd = bcrypt.generate_password_hash(pwd).decode('utf-8')
		device = get_user_device(user, request.user_agent)
		device.status = "Active"
		db.session.commit()
		update_session(user)
		log_activity("Changed Password", user.phone)
		flash("Password Changed Successfully!", category = "success")
		return redirect('/')
	return render_template('reset_pass.html', records = user)

@app.route('/add_device', methods = ['GET', 'POST'])
def add_device():
	if request.method == "POST":
		code = request.form['code']
		user = User.query.filter_by(code = code).first()
		device = get_user_device(user, request.user_agent)
		device.status = "Active"
		user.code = None
		db.session.commit()
		update_session(user)
		flash("New device {} added!".format(device.name), "success")
		return redirect('/')
	return render_template('add_device.html', records = "code")

def get_user_device(user, data):
	data_hash = hashlib.sha256(str(data).encode()).hexdigest()
	device = User_device.query.filter_by(user_id = user.id, data = data_hash).first()
	if not device:
		systems = ["Ubuntu", "Linux", "Windows"]
		browsers = ["Firefox", "Chrome"]
		name = ""
		for item in systems:
			if item in str(data):
				name = name + item + " "
		for item in browsers:
			if item in str(data):
				name = name + item
		device = User_device(name = name, data = data_hash)
		user.devices.append(device)
		db.session.commit()
	return device

@app.route('/logs/<no>')
@verify_super_admin
def logs(no):
	session['previous'] = "/logs/{}".format(no)
	d = datetime.today()
	no = int(no)
	d = d + timedelta(days=no)
	data_filter = d.strftime("%d %B, %Y")
	get_log("Logs", data_filter)
	logs = Log.query.filter(Log.time.like('%'+ data_filter +'%')).all()
	data = {'logs': logs, 'no': int(no), 'period': data_filter}
	return render_template('samis_admin/logs.html', records = data)

def get_school():
	school_id = int(session['samis'])
	school = db.session.get(School, school_id)
	return school

#System Super admin
@app.route('/samis/<page>/<ids>')
@verify_super_admin
def samis_admin(page, ids):
	get_log("Super Admin", page + "/" + ids)
	session['previous'] = "/samis/{}/{}".format(page, ids)
	if ids == session['user']['uuid']:
		if page == "school":
			data = {'schools': School.query.all(), 'modules': Service.query.all()}
		elif page == "user":
			data = {'users': User.query.all()}
		#elif page == "config":
		#	data = {'configs': Configuration.query.all()}
		elif page == "module":
			data = {'modules': Service.query.all()}
		return render_template('samis_admin/' + page + 's.html', records = data)
	else:
		if page == "school":
			school = School.query.filter_by(uuid = ids).first()
			modules = Service.query.all()
			for subscription in school.subscriptions:
				modules.remove(subscription.service)
			data = {'school': school, 'modules': modules}
		#elif page == "config":
		#	data = {'configs': Configuration.query.all()}
		return render_template('samis_admin/' + page + '.html', records = data)

def invalid_link(item):
	if not item:
		return redirect('/')

@app.route('/suspend_school', methods = ['POST'])
@verify_super_admin
def suspend_school():
	remarks = request.form['remarks']
	status = request.form['status']
	school_id = int(request.form['school_id'])
	school = db.session.get(School, school_id)
	school.status = status
	change = "Activated" if status == "Active" else status
	change = Samis_Activity(uuid = uuid.uuid1().hex, school_id = school.id, change = change, remarks = remarks, date = get_time("date"))
	db.session.add(change)
	db.session.commit()
	return redirect(session['previous'])

@app.route('/subscribe', methods = ['POST'])
@verify_super_admin
def subscribe():
	#remarks = request.form['remarks']
	service_id = int(request.form['service_id'])
	school_id = int(request.form['school_id'])
	school = db.session.get(School, school_id)
	service = db.session.get(Service, service_id)
	date = get_time("date")
	subscription = Subscription(uuid = uuid.uuid1().hex, school_id = school.id, service_id = service_id, date = date)
	change = Samis_Activity(uuid = uuid.uuid1().hex, school_id = school.id, change = "New Subscription", remarks = service.name, date = date)
	db.session.add_all([subscription, change])
	db.session.commit()
	return redirect(session['previous'])

@app.route('/new_school', methods = ['GET', 'POST'])
@verify_super_admin
def new_school():
		name = request.form['name']
		phone = request.form['phone']
		email = request.form['email']
		address = request.form['address']
		manager = request.form['user']
		designation = request.form['designation']
		user_no = request.form['user_no']
		modules = request.form.getlist('modules')
		#code = random.randint(100000, 999999)
		user = User.query.filter_by(phone = user_no).first()
		if not user:
			school = School(uuid = uuid.uuid1().hex, name = name, phone = phone, address = address)
			db.session.add(school)
			db.session.commit()
			db.session.refresh(school)
			for item in modules:
				subscription = Subscription(uuid = uuid.uuid1().hex, school_id = school.id, service_id = int(item))
				db.session.add(subscription)
			school.config = School_configuration(uuid = uuid.uuid1().hex)
			department = Department(uuid = uuid.uuid1().hex, school_id = school.id, name = "Administration", description = "School admin and finance")
			db.session.add(department)
			db.session.commit()
			db.session.refresh(department)
			rights = "Admin, Receive, Issue"
			add_user(school.id, department.id, manager, user_no, designation, rights)
			flash("The school {} was added Successfully".format(name), category = "success")
		else:
			flash("The phone number has already been resgistered in the system!", "danger")
		return redirect(session['previous'])

@app.route('/user_logs/<no>')
@verify_admin
def user_logs(no):
	session['previous'] = "/user_logs/{}".format(no)
	#school_id = int(session['samis'])
	school = get_school()
	get_log("User Logs", no)
	user = User.query.filter_by(uuid = no).first()
	logs = user.logs if user else school.user_logs
	data = {'logs': logs}
	return render_template('admin/user_logs.html', records = data)

@app.route('/deleted_items/<no>')
@verify_admin
def deleted_items(no):
	session['previous'] = "/deleted_items/{}".format(no)
	school_id = int(session['samis'])
	get_log("Deleted Items", no)
	deleted_items = Deleted_item.query.filter_by(school_id = school_id).all()
	data = {'deleted_items': deleted_items}
	return render_template('admin/deleted_items.html', records = data)

@app.route('/shortcuts')
@verify_session
def view_shortcuts():
	session['previous'] = "/shortcuts"
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	return render_template('shortcuts.html', records = user.shortcuts)

@app.route('/profile/<category>', methods = ['GET', 'POST'])
@verify_session
def view_profile(category):
	session['previous'] = "/profile/{}".format(category)
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	if request.method == "POST":
		if category == "check":
			password = request.form['password']
			if bcrypt.check_password_hash(user.pwd, password):
				flash("A message was sent to {}".format(user.phone), "success")
				user.code = random.randint(100000, 999999)
				text = "Use the code {} to change your details.".format(user.code)
				send_text(user.phone, text, "SAMIS Admin")
			else:
				flash("You entered the wrong password!", "danger")
				category = "view"
		else:
			code = request.form['code']
			phone = request.form['phone']
			check_user = User.query.filter_by(phone = phone).first()
			if not check_user:
				if user.code == code:
					user.phone = phone
					user.code = None
					flash("Phone Number changed Successfully!", "success")
					category = "view"
				else:
					flash("You entered the wrong code! Please try again", "danger")
					category = "check"
			else:
				flash("Phone number already exists in the system! Please Login.", "danger")
		db.session.commit()
	return render_template('profile.html', records = {'user': user, 'category': category})

@app.route('/shortcut/<category>', methods = ['POST'])
@verify_session
def add_shortcut(category):
	link = request.form['link']
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	shortcut = Shortcut.query.filter_by(link = link, user_id = user.id).first()
	if shortcut:
		shortcut.status = "Active"
		db.session.commit()
		flash("The shortcut already exists!", category = "danger")
		return redirect('/')
	elif category == "add":
		data = {'link': link, 'address': request.access_route[-1]}
		return render_template('/shortcut.html', records = data)
	else:
		name = request.form['name']
		icon = request.form['icon']
		description = request.form['description']
		log_activity("Added Shortcut", link)
		shortcut = Shortcut(uuid = uuid.uuid1().hex, user_id = user.id, name = name, description = description, link = link, icon = icon)
		db.session.add(shortcut)
		db.session.commit()
		return redirect('/')

@app.route('/settings/<page>')
@verify_admin
def system_data(page):
	session['previous'] = "/settings/{}".format(page)
	data_items = ["Department", "Employee", "Supplier", "Unit", "Store", "Product"]
	school_id = int(session['samis'])
	#school = db.session.get(School, school_id)
	school = get_school()
	employees = get_school_data("employees")
	data = {'school': school, 'employees': employees}
	if page == "all":
		settings = []
		for item in data_items:
			if item == "Employee":
				settings.append({'name': item, 'no': len(employees)})
			else:
				item_class = getattr(sys.modules[__name__], item)
				settings.append({'name': item, 'no': item_class.query.filter_by(school_id = school_id).count()})
		data['settings'] = settings
		data['user'] = User.query.filter_by(uuid = session['user']['uuid']).first()
		data_items.remove("Employee")
		data['data_items'] = data_items
		return render_template('admin/system_datas.html', records = data)
	else:
		data_item = page.title()
		data['category'] = data_item
		if data_item == "Employee":
			data['data_items'] = employees
		else:
			item_class = getattr(sys.modules[__name__], data_item)
			data['data_items'] = item_class.query.filter_by(school_id = school_id, deleted = False).all()
		return render_template('admin/system_data.html', records = data)

@app.route('/add_system_data', methods = ['GET', 'POST'])
def add_system_data():
	category = request.form['category']
	name = request.form['name']
	item_id = int(request.form['item_id'])
	item_class = getattr(sys.modules[__name__], category)
	item = item_class.query.filter_by(school_id = item_id, name = name).first()
	if item:
		flash("The {} - {} already exists!".format(category, name), "danger")
	else:
		item = item_class(uuid = uuid.uuid1().hex, school_id = item_id, name = name)
		db.session.add(item)
		db.session.commit()
	return redirect(session['previous'])

@app.route('/edit_data/<category>', methods = ['POST'])
@verify_session
def edit_data(category):
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	school_id = int(session['samis'])
	#school = db.session.get(School, school_id)
	school = get_school()
	if category == "data":
		user.employee.name = request.form['name']
		school.name = request.form['school']
		school.address = request.form['address']
		school.motto = request.form['motto']
		log_activity("Editted", "School Details")
	elif category == "logo":
		logo_id = uuid.uuid1().hex
		uploaded_file = request.files['logo']
		if uploaded_file.filename != '':
			file_ext = os.path.splitext(uploaded_file.filename)[1]
			filename = logo_id  + file_ext
			log_activity("Uploaded", "School Logo")
			school.logo = filename
			uploaded_file.save(os.path.join('./static/images/photos/', filename))
	db.session.commit()
	update_session(user)
	return redirect(session['previous'])

@app.route('/report/<page>')
@verify_session
@verify_school_status
def report(page):
	get_log("report", page)
	school_id = int(session['samis'])
	session['previous'] = "/report/{}".format(page)
	log_activity("Printed", "{} Report".format(page))
	products = Product.query.filter_by(category = page, school_id = school_id).all()
	data = {'products': products, 'date': get_time("date")}
	return render_template('report/{}.html'.format(page), records = data)

@app.route('/reset/<category>/<uuid>')
@verify_session
def reset(category, uuid):
	if category == "order":
		item = Order_item.query.filter_by(uuid = uuid).first()
		item.quantity = 0
		update_order(item.purchase_order)
	elif category == "request":
		item = RQ_item.query.filter_by(uuid = uuid).first()
		item.quantity = 0
	elif category == "shortcut":
		item = Shortcut.query.filter_by(uuid = uuid).first()
		item.status = "Inactive"
	log_activity("Reset Data", "{} No {}".format(category, item.id))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/delete/<item>/<ids>')
@verify_admin
def delete(item, ids):
	date = get_time("date")
	school_id = int(session['samis'])
	item_class = getattr(sys.modules[__name__], item.title())
	the_item = item_class.query.filter_by(uuid = ids).first()
	the_item.deleted = True
	deleted_item = Deleted_item.query.filter_by(category = item, item_id = the_item.id).first()
	if not deleted_item:
		deleted_item = Deleted_item(uuid = uuid.uuid1().hex, school_id = school_id, category = item, name = the_item.name, item_id = the_item.id, date = date)
		db.session.add(deleted_item)
	else:
		deleted_item.status = "Removed"
		deleted_item.date = date
	db.session.commit()
	log_activity("Deleted {}".format(item), deleted_item.name)
	return redirect(session['previous'])

@app.route('/restore/<ids>')
@verify_admin
def restore(ids):
	date = get_time("date")
	item = Deleted_item.query.filter_by(uuid = ids).first()
	item_class = getattr(sys.modules[__name__], item.category.title())
	the_item = db.session.get(item_class, item.item_id)
	the_item.deleted = False
	item.status = "Restored"
	db.session.commit()
	log_activity("Restored deleted {}".format(item.category), item.name)
	return redirect(session['previous'])

#INVENTORY MODULE PAGE ROUTING
@app.route('/inventory/<page>/<ids>')
@verify_session
@verify_school_status
def inventory(page, ids):
	get_log("inventory", page + "/" + ids)
	session['previous'] = "/inventory/{}/{}".format(page, ids)
	school_id = int(session['samis'])
	school = db.session.get(School, school_id)
	if ids == "ujuzi" or ids == session['user']['uuid']:
		if page == "department":
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'departments': departments}
		elif page == "supplier":
			suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'suppliers': suppliers}
		elif page == "employee":
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			employees = get_school_data("employees")
			data = {'departments': departments, 'employees': employees}
		elif page == "stock":
			products = Product.query.filter_by(deleted = False, school_id = school_id).all()
			suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			employees = get_school_data("employees")
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			units = Unit.query.filter_by(deleted = False, school_id = school_id).all()
			data ={'stock': products, 'suppliers': suppliers, 'stores': stores, 'employees': employees, 'departments': departments, 'units': units}
		elif page == "asset":
			assets = get_school_data("assets")
			employees = get_school_data("employees")
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			asset_types = Product.query.filter(Product.category != "s1", Product.deleted == False, Product.school_id == school_id).all()
			data = {'assets': assets,'asset_types':asset_types, 'employees': employees, 'stores': stores, 'departments': departments}
		elif page == "receipt":
			receipts = get_school_data("po_items")
			data = {'receipts': receipts}
		elif page == "issue":
			issues = get_school_data("rq_items")
			data = {'issues': issues}
		elif page == "store":
			employees = get_school_data("employees")
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'stores': stores, 'employees': employees}
		elif page == "inward":
			data = {'inwards': get_school_data("inwards")}
		elif page == "outward":
			data = {'outwards': get_school_data("outwards")}
		elif page == "order":
			suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
			products = Product.query.filter_by(deleted = False, school_id = school_id).all()
			orders = Purchase_order.query.filter_by(school_id = school_id).all()
			filters = ["draft", "locked", "completed", "cancelled"]
			session['filter'] = filters[0] if session['filter'] not in filters else session['filter']
			data = {'orders': orders, 'suppliers': suppliers, 'products': products, 'filters': filters}
		elif page == "request":
			requests = Request_quantity.query.filter_by(school_id = school_id).all()
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			stock = get_school_data("stock")
			filters = ["draft", "completed", "cancelled"]
			session['filter'] = filters[0] if session['filter'] not in filters else session['filter']
			data = {'requests': requests, 'departments': departments, 'stock': stock, 'filters': filters}
		elif page == "release":
			rq_items = [ item for item in get_school_data("rq_items") if item.assets > 0]
			data = {'products': rq_items}
		elif page == "reorder":
			products = [product for product in school.products if product.reorder_level > product.quantity]
			suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'products': products, 'suppliers': suppliers}
		return render_template('inventory/' + page + 's.html', records = data)
	else:
		data = None
		if page == "department":
			products = []
			stock = get_school_data("stock")
			department = Department.query.filter_by(uuid = ids).first()
			for item in department.assets:
				products.append(item.product.name)
			assets = {i:products.count(i) for i in products}
			data = {'department': department, 'products': products, 'stock': stock, 'assets': assets}
		elif page == "employee":
			employee = Employee.query.filter_by(uuid = ids).first()
			data = {'employee': employee}
		elif page == "supplier":
			supplier = Supplier.query.filter_by(uuid = ids).first()
			data = {'supplier': supplier}
		elif page == "store":
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			products = Product.query.filter_by(category = "s1", deleted = False, school_id = school_id).all()
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			suppliers = Supplier.query.filter_by(deleted = False, school_id = school_id).all()
			store = Store.query.filter_by(uuid = ids).first()
			employees = get_school_data("employees")
			data = {'store': store, 'products': products, 'suppliers': suppliers, 'departments': departments, 'stores': stores, 'employees': employees}
		elif page == "product":
			product = Product.query.filter_by(uuid = ids).first()
			units = Unit.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'product': product, 'units': units}
		elif page == "asset_type":
			asset_type = Product.query.filter_by(uuid = ids).first()
			data = {'asset_type': asset_type}
		elif page == "asset" or page == "maintenance" or page == "depreciation":
			asset = Asset.query.filter_by(uuid = ids).first()
			employees = get_school_data("employees")
			departments = Department.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'asset': asset, 'employees': employees, 'departments': departments}
		elif page == "order":
			order = Purchase_order.query.filter_by(uuid = ids).first()
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			order_items = order.order_items
			products = Product.query.filter_by(deleted = False, school_id = school_id).all()
			delete_items = [ {'category': "Order Item", 'uuid': item.uuid, 'name': item.product.name, 'link': "/reset/order/{}".format(item.uuid)} for item in order_items]
			data = {'order': order, 'products': products, 'order_items': order_items, 'stores': stores, 'delete_items': delete_items}
		elif page == "po_item":
			order_item = Order_item.query.filter_by(uuid = ids).first()
			data = {'order_item': order_item}
		elif page == "request":
			stock = get_school_data("stock")
			request = Request_quantity.query.filter_by(uuid = ids).first()
			employees = request.department.employees
			delete_items = [ {'category': "Requested Item", 'uuid': item.uuid, 'name': item.stock.product.name, 'link': "/reset/request/{}".format(item.uuid)} for item in request.rq_items]
			data = {'request': request, 'stock': stock, 'employees': employees, 'delete_items': delete_items}
		elif page == "release":
			data = {'rq_item': RQ_item.query.filter_by(uuid = ids).first()}
		elif page == "return":
			department = Department.query.filter_by(uuid = ids).first()
			stores = Store.query.filter_by(deleted = False, school_id = school_id).all()
			data = {'department': department, 'stores': stores}
		elif page == "guide":
			data = None
		return render_template('inventory/' + page + '.html', records = data)

@app.route('/new/<item>', methods = ['POST'])
@verify_session
def new_item(item):
	get_log("New Item", item)
	name = request.form['name']
	school_id = int(session['samis'])
	the_item = None
	if item != "asset_type" and item != "asset" and item != "employee":
		item_class = getattr(sys.modules[__name__], item.title())
		the_item = item_class.query.filter_by(name = name, school_id = school_id).first()
	if not the_item:
		log_activity("Created", "New {}: {}".format(item, name))
		if item == "product":
			cost = float(request.form['cost'])
			description = request.form['description']
			unit_id = int(request.form['unit_id'])
			unit = request.form['unit']
			if unit_id == 0:
				unit = Unit(uuid = uuid.uuid1().hex, name = unit)
				db.session.add(unit)
				db.session.commit()
				db.session.refresh(unit)
				unit_id = unit.id
			if cost > 0:
				new_item = Product(uuid = uuid.uuid1().hex, school_id = school_id, unit_id = unit_id, name = name, cost = cost, description = description)
			else:
				flash("Invalid unit cost entered for {}!".format(name), category = "danger")
				return redirect(session['previous'])
		elif item == "employee":
			department_id = int(request.form['department_id'])
			location = request.form['location']
			employees = [ employee for employee in get_school_data("employees") if employee.name == name]
			if len(employees) > 0:
				flash("The Employee, {} already exists in the system!".format(name), category = "danger")
				return redirect(session['previous'])
			else:
				new_item = Employee(uuid = uuid.uuid1().hex, department_id = department_id, name = name, location = location)
		elif item == "supplier":
			phone = request.form['phone']
			address = request.form['address']
			new_item = Supplier(uuid = uuid.uuid1().hex, school_id = school_id, name = name, phone = phone, address = address)
		elif item == "store":
			location = request.form['location']
			manager_id = int(request.form['manager_id'])
			new_item = Store(uuid = uuid.uuid1().hex, school_id = school_id, name = name, manager_id = manager_id, location = location)
		elif item == "department":
			description = request.form['description']
			new_item = Department(uuid = uuid.uuid1().hex, school_id = school_id, name = name, description = description)
		elif item == "asset":
			asset_type_id = int(request.form['asset_type_id'])
			serial = request.form['serial']
			description = request.form['description']
			depreciation = request.form['depreciation']
			owner_id = int(request.form['owner_id'])
			#store_id = int(request.form['store_id'])
			location = request.form['location_id']
			item_id = location[location.index(" "):]
			value = float(request.form['value'])
			date = request.form['date']
			product = db.session.get(Product, asset_type_id)
			if "store" in location:
				stock = get_stock(product.id, item_id)
				stock.quantity = stock.quantity + 1
				item_id = None
			#stock = get_stock(product.id, store_id)
			product.quantity = product.quantity + 1
			#stock.quantity = stock.quantity + 1
			rate = 0 if depreciation == "" else float(depreciation)
			asset = Asset.query.filter_by(name = name, product_id = asset_type_id).first()
			if asset:
				flash("The Asset, {} already exists in the system!".format(name), category = "danger")
				return redirect(session['previous'])
			else:				
				new_item = Asset(uuid = uuid.uuid1().hex, name = name, owner_id = owner_id, product_id = product.id, department_id = item_id, serial = serial, description = description, depreciation = rate, value = value, acquired_on = date)
		elif item == "asset_type":
			category = request.form['category']
			product = Product.query.filter_by(name = name, school_id = school_id).first()
			if product:
				flash("The Asset Type, {} already exists in the system!".format(name), category = "danger")
				return redirect(session['previous'])
			else:
				new_item = Product(uuid = uuid.uuid1().hex, school_id = school_id, name = name, category = category)
		elif item == "unit":
			sub_unit = request.form['sub_unit']
			sub_value = float(request.form['sub_value']) if request.form['sub_value'] != "" else 0
			new_item = Unit(uuid = uuid.uuid1().hex, school_id = school_id, name = name, sub_unit = sub_unit, sub_value = sub_value)
		if new_item:
			db.session.add(new_item)
		db.session.commit()
	else:
		flash("The {}, {}, already exists in the System!".format(item, name), category = "danger")
	return redirect(session['previous'])

@app.route('/new_user', methods = ['POST'])
@verify_admin
def new_user():
	name = request.form['name']
	phone = request.form['phone']
	designation = request.form['designation']
	rights = request.form.getlist('rights')
	module = request.form['module']
	school = School.query.filter_by(uuid = session['school']['uuid']).first()
	department = Department.query.filter_by(name = module).first()
	roles = ', '.join(rights)
	log_activity("Created new user", name)
	add_user(school.id, department.id, name, phone, designation, roles)
	return redirect(session['previous'])

def add_user(school_id, department_id, name, phone, designation, rights):
	code = random.randint(100000, 999999)
	school = db.session.get(School, school_id)
	employee = Employee(uuid = uuid.uuid1().hex, department_id = department_id, name = name, designation = designation)
	db.session.add(employee)
	#db.session.commit()
	#db.session.refresh(employee)
	user = User(uuid = uuid.uuid1().hex, school_id = school_id, phone = phone, rights = rights, code = code)
	employee.user = user
	#db.session.add(employee)
	db.session.commit()
	#text = "Hello {}.\n{} has resgistered you as a {}. \nGo to {}reset_pass/code to set your password.".format(name, school.name, designation, request.host_url)
	text = "Hello {}.\n{} has resgistered you as a {}.\nPlease set a new password.".format(name, user.school.name, employee.designation)
	send_text(phone, text, "SAMIS Admin")

@app.route('/add_stock', methods = ['POST'])
@verify_session
def add_stock():
	get_log("Add", "Stock")
	product_id = int(request.form['product_id'])
	store_id = int(request.form['store_id'])
	quantity = float(request.form['quantity'])
	date = get_time("date")
	product = db.session.get(Product, product_id)
	log_activity("Added Stock", "{} {} of {}".format(quantity, product.unit.name, product.name))
	total_quantity = product.quantity + quantity
	stock = get_stock(product_id, store_id)
	stock.quantity = stock.quantity + quantity
	product.quantity = total_quantity
	details = "New stock added to {} mannually".format(stock.store.name)
	stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = quantity, balance = total_quantity, date = date)
	db.session.add(stock_log)
	db.session.commit()
	return redirect(session['previous'])

@app.route('/move_stock', methods = ['POST'])
@verify_session
def move_stock():
	get_log("Move", "Stock")
	stock_id = int(request.form['stock_id'])
	store_id = int(request.form['store_id'])
	quantity = float(request.form['quantity'])
	stock = db.session.get(Stock, stock_id)
	date = get_time("date")
	if check_availability(stock, quantity):
		stock.quantity = stock.quantity - quantity
		new_stock = get_stock(stock.product_id, store_id)
		new_stock.quantity = new_stock.quantity + quantity
		details = "Moved {} {} from {} to {}".format(quantity, stock.product.unit.name, stock.store.name, new_stock.store.name)
		stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = stock.product.id, details = details, quantity = 0, balance = stock.product.quantity, date = date)
		log_activity("Moved Stock", "From {} to {}".format(stock.store.name, new_stock.store.name))
		db.session.add(stock_log)
		db.session.commit()
	else:
		flash("Product not available in Store Selected", category = "danger")
	return redirect(session['previous'])

@app.route('/stock_loss', methods = ['POST'])
@verify_session
def stock_loss():
	get_log("Lose", "Stock")
	stock_id = int(request.form['stock_id'])
	reason = request.form['reason']
	remarks = request.form['remarks']
	quantity = float(request.form['quantity'])
	stock = db.session.get(Stock, stock_id)
	date = get_time("date")
	if check_availability(stock, quantity):
		quantity = 0 - quantity
		stock.quantity = stock.quantity + quantity
		stock.product.quantity = stock.product.quantity + quantity
		#new_stock = get_stock(stock.product_id, store_id)
		#new_stock.quantity = new_stock.quantity + quantity
		details = "Lost to {}. {}".format(reason, remarks)
		stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = stock.product.id, details = details, quantity = quantity, balance = stock.product.quantity, date = date)
		log_activity("Stock Loss", "{} from {}".format(stock.product.name, stock.store.name))
		db.session.add(stock_log)
		db.session.commit()
	else:
		message = "You selected to remove items not available in the store!"
		flash(message, category = "danger")
	return redirect(session['previous'])

@app.route('/new_po/<category>', methods = ['POST'])
@verify_session
def new_po(category):
	supplier_id = int(request.form['supplier_id'])
	product_id = int(request.form['product_id'])
	specification = request.form['specification']
	quantity = float(request.form['quantity'])
	school_id = int(session['samis'])
	school = db.session.get(School, school_id)
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	date = get_time("date")
	order_no = school.config.last_po + 1
	school.config.last_po = order_no
	order = Purchase_order(uuid = uuid.uuid1().hex, school_id = school_id, user_id = user.id, supplier_id = supplier_id, date = date, no = order_no)
	db.session.add(order)
	db.session.commit()
	db.session.refresh(order)
	product = db.session.get(Product, product_id)
	order_item = Order_item(uuid = uuid.uuid1().hex, product_id = product_id, purchase_order_id = order.id, specification = specification, quantity = quantity)
	if product.category == "s1":
		order_item.price = product.cost
		order.value = quantity * product.cost
	db.session.add(order_item)
	log_activity("Created", "Order No {} with {} {}".format(order.no, quantity, product.name))
	db.session.commit()
	return redirect('/inventory/order/{}'.format(order.uuid))

@app.route('/new_rq', methods = ['POST'])
@verify_session
def new_rq():
	stock_id = int(request.form['stock_id'])
	department_id = int(request.form['department_id'])
	quantity = float(request.form['quantity'])
	date = get_time("date")
	stock = db.session.get(Stock, stock_id)
	school_id = int(session['samis'])
	school = db.session.get(School, school_id)
	request_no = school.config.last_rq + 1
	school.config.last_rq = request_no
	user = User.query.filter_by(uuid = session['user']['uuid']).first()
	if check_availability(stock, quantity):
		rq = Request_quantity(uuid = uuid.uuid1().hex, user_id = user.id, school_id = school_id, department_id = department_id, date = date, no = request_no)
		db.session.add(rq)
		db.session.commit()
		db.session.refresh(rq)
		rq_item = RQ_item(uuid = uuid.uuid1().hex, stock_id = stock.id, request_quantity_id = rq.id, quantity = quantity)
		db.session.add(rq_item)
		log_activity("Created", "Request No {} with {} {}".format(rq.no, quantity, stock.product.name))
		db.session.commit()
		return redirect('/inventory/request/{}'.format(rq.uuid))
	else:
		flash("Product not available in Store Selected", category = "danger")
		return redirect(session['previous'])

@app.route('/add_po_items', methods = ['POST'])
@verify_session
def add_po_items():
	product_id = int(request.form['product_id'])
	quantity = float(request.form['quantity'])
	item_id = int(request.form['item_id'])
	specification = request.form['specification']
	date = get_time("date")
	po = db.session.get(Purchase_order, item_id)
	is_new = True
	product = db.session.get(Product, product_id)
	for item in po.order_items:
		if item.product_id == product_id:
			if item.specification == specification:
				item.quantity = item.quantity + quantity
				po_item = item
				is_new = False
	if is_new:
		po_item = Order_item(uuid = uuid.uuid1().hex, product_id = product_id, purchase_order_id = po.id, specification = specification, quantity = quantity)
		db.session.add(po_item)
	if product.category == "s1":
		po_item.price = product.cost
		value = quantity * product.cost
		po.value = po.value + value
	log_activity("Updated", "Order No {} with {} {}".format(po.no, quantity, product.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/add_rq_items', methods = ['POST'])
@verify_session
def add_rq_items():
	stock_id = int(request.form['stock_id'])
	quantity = float(request.form['quantity'])
	request_id = int(request.form['request_id'])
	date = get_time("date")
	stock = db.session.get(Stock, stock_id)
	if check_availability(stock, quantity):
		rq = db.session.get(Request_quantity, request_id)
		is_new = True
		for item in rq.rq_items:
			if item.stock_id == stock_id:
				#item.quantity = item.quantity + quantity
				is_new = False
				quantity = item.quantity + quantity
				if check_availability(stock, quantity):
					item.quantity = quantity
					#is_new = False
				else:
					flash("Product not available in Store Selected", category = "danger")
		if is_new:
			rq_item = RQ_item(uuid = uuid.uuid1().hex, request_quantity_id = request_id, stock_id = stock_id, quantity = quantity)
			db.session.add(rq_item)
		rq.status = "updated"
		log_activity("Updated", "Request No {} with {} {}".format(rq.no, quantity, stock.product.name))
		db.session.commit()
	else:
		flash("Product not available in Store Selected", category = "danger")
	return redirect(session['previous'])

@app.route('/edit_price', methods = ['POST'])
@verify_session
def edit_price():
	item_id = int(request.form['item_id'])
	price = float(request.form['price'])
	item = db.session.get(Order_item, item_id)
	order = item.purchase_order
	item.price = price
	log_activity("Updated", "Price of {} to {}".format(item.product.name, price))
	db.session.commit()
	update_order(order)
	return redirect(session['previous'])

@app.route('/receive_po_items', methods = ['POST'])
@verify_session
def receive_po_items():
	order_id = int(request.form['order_id'])
	store_id = int(request.form['store_id'])
	order = db.session.get(Purchase_order, order_id)
	date = date = get_time("date")
	for item in order.order_items:
		product = item.product
		initial_quantity = product.quantity
		total_quantity = initial_quantity + item.quantity
		stock = get_stock(product.id, store_id)
		stock.quantity = stock.quantity + item.quantity
		item.stock_id = stock.id
		product.quantity = total_quantity
		details = "Received at {} from {}".format(stock.store.name, order.supplier.name)
		stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = item.quantity, balance = total_quantity, date = date)
		db.session.add(stock_log)
		if item.product.category == "s1":
			total_cost = product.cost * initial_quantity + item.price * item.quantity
			product.cost = total_cost / total_quantity
			product.description = item.specification
		else:
			count = item.quantity
			while(count != 0):
				code = Asset.query.filter_by(product_id = item.product_id).count()
				name = "{} {}".format(product.name, code)
				asset = Asset(uuid = uuid.uuid1().hex, name = name, serial = name, product_id = item.product_id, order_item_id = item.id, description = item.specification, value = item.price, acquired_on = date)
				db.session.add(asset)
				db.session.commit()
				db.session.refresh(asset)
				details = "New {} acquired".format(product.name)
				remarks = "Bought from {}".format(order.supplier.name)
				activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = date)
				db.session.add(activity)
				count = count - 1
	order.status = "completed"
	log_activity("Received", "Items for Order No {}".format(order.no))
	db.session.commit()
	return redirect('/inventory/order/ujuzi')

@app.route('/edit_asset/<category>', methods = ['POST'])
@verify_session
def edit_asset(category):
	asset_id = int(request.form['asset_id'])
	asset = db.session.get(Asset, asset_id)
	if category == "details":
		asset.name = request.form['name']
		asset.serial = request.form['serial']
		asset.tag = request.form['tag']
		asset.description = request.form['description']
	elif category == "metrics":
		asset.service = int(request.form['service'])
		asset.waranty = int(request.form['waranty'])
		asset.depreciation = float(request.form['depreciation'])
		waranty_expirery = datetime.strptime(asset.acquired_on, '%d %B, %Y') + timedelta(days=(30 * asset.waranty))
	asset.status = "stored"
	log_activity("Edited", "Details for {} {}".format(asset.product.name, asset.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/edit_item/<category>', methods = ['POST'])
@verify_session
def edit_item(category):
	item_id = int(request.form['item_id'])
	if category == "product":
		item = db.session.get(Product, item_id)
		item.name = request.form['name']
		item.description = request.form['description']
		item.reorder_level = float(request.form['reorder_level'])
		item.reorder_quantity = float(request.form['reorder_quantity'])
	elif category == "measuring_unit":
		item = db.session.get(Product, item_id)
		unit_id = int(request.form['unit_id'])
		if unit_id == 0:
			unit = Unit(uuid = uuid.uuid1().hex, name = request.form['unit'])
			db.session.add(unit)
			db.session.commit()
			db.session.refresh(unit)
			unit_id = unit.id
		item.unit_id = unit_id
		item.cost = float(request.form['cost'])
	elif category == "store":
		item = db.session.get(Store, item_id)
		item.name = request.form['name']
		item.location = request.form['location']
	elif category == "department":
		item = db.session.get(Department, item_id)
		item.name = request.form['name']
		item.description = request.form['description']
	elif category == "employee":
		item = db.session.get(Employee, item_id)
		item.name = request.form['name']
		item.phone = request.form['phone']
	elif category == "supplier":
		item = db.session.get(Supplier, item_id)
		item.name = request.form['name']
		item.phone = request.form['phone']
		item.address = request.form['address']
	log_activity("Editted {}".format(category), "Details for {}".format(item.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/assign/<category>', methods = ['POST'])
@verify_session
def assign(category):
	item_id = int(request.form['item_id'])
	employee_id = int(request.form['employee_id'])
	employee = db.session.get(Employee, employee_id)
	if category == "asset":
		asset = db.session.get(Asset, item_id)
		asset.owner_id = employee_id
		asset.status = "in use"
		details = "Assigned to {}".format(employee.name)
		remarks = "Condition is OK"
		activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = get_time("date"))
		db.session.add(activity)
		log_activity("Assign", "Assigned {}: {} to {}".format(asset.product.name, asset.name, employee.name))
	elif category == "store":
		store = db.session.get(Store, item_id)
		store.manager_id = employee_id
		log_activity("Assign", "Assigned {}: {} to {}".format("Store", store.name, employee.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/move/<category>', methods = ['POST'])
@verify_session
def move(category):
	asset_id = int(request.form['asset_id'])
	department_id = int(request.form['department_id'])
	asset = db.session.get(Asset, asset_id)
	department = db.session.get(Department, department_id)
	asset.department_id = department_id
	asset.status = "in use"
	details = "Moved to {}".format(department.name)
	remarks = "Condition is OK"
	activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = get_time("date"))
	db.session.add(activity)
	log_activity("Moved", "{}, {} to {}".format(asset.product.name, asset.name, department.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/dispose/<category>', methods = ['POST'])
@verify_session
def dispose(category):
	asset_id = int(request.form['asset_id'])
	asset = db.session.get(Asset, asset_id)
	asset.status = "disposed"
	details = "Disposed"
	activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, date = get_time("date"))
	db.session.add(activity)
	asset.product.quantity = asset.product.quantity - 1
	log_activity("Disposed", "{}: {}".format(asset.product.name, asset.name))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/release_rq_items', methods = ['POST'])
@verify_session
def release_rq_items():
	request_id = int(request.form['request_id'])
	employee_id = request.form['employee_id']
	date = date = get_time("date")
	rq = db.session.get(Request_quantity, request_id)
	employee = db.session.get(Employee, employee_id)
	to_release = False
	unavailable = []
	for item in rq.rq_items:
		stock = item.stock
		product = item.stock.product
		quantity = 0 - item.quantity
		total_quantity = product.quantity + quantity
		stock_quantity = stock.quantity + quantity
		if stock_quantity < 0:
			unavailable.append(product.name)
		stock.quantity = stock_quantity
		product.quantity = total_quantity
		details = "Issued to {} at {} from {}".format(employee.name, rq.department.name, item.stock.store.name)
		stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = quantity, balance = total_quantity, date = date)
		db.session.add(stock_log)
		if product.category != "s1":
			item.assets = item.quantity
			to_release = True
	rq.status = "completed"
	if len(unavailable) > 0:
		unavailable_items = ', '.join(unavailable)
		error_text = "The following products are unavailable in the store: {}".format(unavailable_items)
		#return render_template('error.html', records = {'title': "Stock Error", 'data': error_text})
		flash(error_text, category = "danger")
		return redirect(session['previous'])
	else:
		db.session.commit()
		log_activity("Released to {}".format(employee.name), "Items for Request No {}".format(rq.no))
		if to_release:
			return redirect('/inventory/release/ujuzi')
		else:
			return redirect('/inventory/request/ujuzi')

@app.route('/release_assets', methods = ['POST'])
@verify_session
def release_assets():
	assets = request.form.getlist('assets')
	item_id = request.form['item_id']
	rq_item = db.session.get(RQ_item, item_id)
	quantity = len(assets)
	if quantity > rq_item.assets:
		flash("The items selected are more that those requested!", category = "danger")
		return redirect(session['previous'])
	else:
		rq_item.assets = rq_item.assets - quantity
		for item in assets:
			asset = db.session.get(Asset, item)
			asset.department_id = rq_item.request.department_id
		db.session.commit()
		log_activity("Released", "Assets for Request No {}".format(rq_item.request.no))
		return redirect('inventory/release/ujuzi')

def error_message(message):
	flash(message, category = "danger")
	return redirect(session['previous'])

def check_duplicate(category, name):
	item_class = getattr(sys.modules[__name__], category)
	item = item_class.query.filter_by(school_id = school_id, name = name).first()
	if item:
		message = "Duplication Error! The {}, {} already exists in the system!".format(category, name)
		flash(message, category = "danger")
		return True
	else:
		return False

@app.route('/return_assets', methods = ['POST'])
@verify_session
def return_assets():
	assets = request.form.getlist('assets')
	department_id = request.form['department_id']
	store_id = int(request.form['store_id'])
	remarks = request.form['remarks']
	department = db.session.get(Department, department_id)
	#store = db.session.get(Store, store_id)
	date = date = get_time("date")
	for item in assets:
		asset = db.session.get(Asset, item)
		stock = get_stock(asset.product_id, store_id)
		asset.department_id = None
		asset.owner_id = None
		asset.product.quantity = asset.product.quantity + 1
		stock.quantity = stock.quantity + 1
		details = "Returned from {}".format(department.name)
		activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = date)
		db.session.add(activity)
	log_activity("Returned assets", "from {} to {}".format(department.name, stock.store.name))
	db.session.commit()
	return redirect('inventory/department/{}'.format(department.uuid))

@app.route('/return/<category>', methods = ['POST'])
@verify_session
def return_stock(category):
	quantity = float(request.form['quantity'])
	item_id = int(request.form['item_id'])
	date = get_time("date")
	if category == "in":
		rq_item = db.session.get(RQ_item, item_id)
		total_returned = rq_item.returned + quantity
		if rq_item.quantity >= total_returned:
			get_log("Return Inwards", rq_item.stock.product.name)
			product = rq_item.stock.product
			total_quantity = product.quantity + quantity
			rq_item.stock.quantity = rq_item.stock.quantity + quantity
			product.quantity = total_quantity
			rq_item.returned = total_returned
			returns = Inward(uuid = uuid.uuid1().hex, rq_item_id = item_id, quantity = quantity, date = date)
			details = "Returned to {} from {}".format(rq_item.stock.store.name, rq_item.request.department.name)
			stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = quantity, balance = total_quantity, date = date)
			db.session.add(stock_log)
		else:
			flash("Unavailable items cannot be returned!", category = "danger")
			return redirect(session['previous'])
	elif category == "out":
		order_item = db.session.get(Order_item, item_id)
		total_returned = order_item.returned + quantity
		if order_item.quantity >= total_returned:
			product = order_item.product
			quantity = 0 - quantity
			total_quantity = product.quantity + quantity
			get_log("Return Outwards", order_item.product.name)
			order_item.stock.quantity = order_item.stock.quantity + quantity
			product.quantity = total_quantity
			order_item.returned = total_returned
			returns = Outward(uuid = uuid.uuid1().hex, order_item_id = item_id, quantity = quantity, date = date)
			details = "Returned to {} from {}".format(order_item.purchase_order.supplier.name, order_item.stock.store.name)
			stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = quantity, balance = total_quantity, date = date)
			db.session.add(stock_log)
		else:
			flash("Unavailable items cannot be returned!", category = "danger")
			return redirect(session['previous'])
	elif category == "asset":
		assets = request.form.getlist('assets')
		quantity = 0 - len(assets)
		order_item = db.session.get(Order_item, item_id)
		product = order_item.product
		total_quantity = product.quantity + quantity
		product.quantity = total_quantity
		returns = Outward(uuid = uuid.uuid1().hex, order_item_id = item_id, quantity = quantity, date = date)
		details = "Returned to {} from {}".format(order_item.purchase_order.supplier.name, order_item.stock.store.name)
		stock_log = Stock_log(uuid = uuid.uuid1().hex, product_id = product.id, details = details, quantity = quantity, balance = total_quantity, date = date)
		db.session.add(stock_log)
		for item in assets:
			asset = db.session.get(Asset, item)
			asset.status = "returned"
		#returns = Asset_return(uuid = uuid.uuid1().hex, quantity = quantity, date = date)
	db.session.add(returns)
	log_activity("Returned {}".format(product.name), details.split(' ', 1)[1])
	db.session.commit()
	return redirect(session['previous'])

@app.route('/depreciate')
@verify_session
def depreciate():
	date = get_time("date")
	year = get_time("year")
	for asset in Asset.query.filter_by(deleted = False).all():
		asset.age = asset.age + 1
		if asset.depreciation != 0:
			amount = asset.depreciation * asset.value / 100
			asset.value = asset.value - amount
			details = "Depreciation for {}".format(year)
			depreciation = Depreciation(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, amount = amount, date = date)
			db.session.add(depreciation)
			details = "Depreciation for {} is {}".format(year, amount)
			remarks = "{}% rate applied".format(asset.depreciation)
			activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = date)
			db.session.add(activity)
	log_activity("Depreciated", "All assets")
	db.session.commit()
	return redirect(session['previous'])

@app.route('/maintain', methods = ['POST'])
@verify_session
def maintain():
	date = get_time("date")
	company = request.form['company']
	technician = request.form['technician']
	asset_id = request.form['asset_id']
	asset = db.session.get(Asset, asset_id)
	no = asset.service * 30
	d = datetime.today() + timedelta(days=no)
	next_service = d.strftime("%d %B, %Y")
	remarks = "Serviced by {} from {}".format(technician, company)
	service = Maintenance(uuid = uuid.uuid1().hex, asset_id = asset.id, details = remarks, date = date, next_service = next_service)
	db.session.add(service)
	details = "{} month service done".format(asset.service)
	activity = Asset_activity(uuid = uuid.uuid1().hex, asset_id = asset.id, details = details, remarks = remarks, date = date)
	db.session.add(activity)
	log_activity("Maintained {}".format(asset.product.name), remarks)
	db.session.commit()
	return redirect(session['previous'])

@app.route('/update_status/<category>', methods = ['POST'])
@verify_session
def update_status(category):
	item_id = int(request.form['item_id'])
	status = request.form['status']
	remarks = request.form['remarks']
	if category == "order":
		item = db.session.get(Purchase_order, item_id)
	elif category == "request":
		item = db.session.get(Request_quantity, item_id)
	item.status = status
	log_activity("Changed status", "of {} No {} to {} due to {}".format(category, item.no, status, remarks))
	db.session.commit()
	return redirect(session['previous'])

@app.route('/update_filter/<item>')
@verify_session
def update_filter(item):
	session['filter'] = item
	return redirect(session['previous'])

#ADMIN MODULE PAGE ROUTING
@app.route('/admin/<page>/<ids>')
@verify_admin
def admin(page, ids):
	get_log("Admin", page + "/" + ids)
	session['previous'] = "/admin/{}/{}".format(page, ids)
	school = get_school()
	#school = School.query.filter_by(uuid = session['school']['uuid']).first()
	if ids == session['user']['uuid']:
		if page == "user":
			data = {'users': school.users}
		return render_template('admin/' + page + 's.html', records = data)
	else:
		if page == "user":
			data = {'user': User.query.filter_by(uuid = ids).first()}
		elif page == "guide":
			data = None
		return render_template('admin/' + page + '.html', records = data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port="6800", debug=False)
