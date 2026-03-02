from samis_stock import *
import time

with open('settings.yaml') as f:
	app_data = yaml.load(f, Loader=yaml.FullLoader)
f.close()

default_phone = app_data['default_phone']
default_email = app_data['default_email']
default_pass = app_data['default_pass']

with app.app_context():
	db.create_all()
	time.sleep(1)
	print("Initializing the system...............")

	if User.query.count() == 0:
		pwd = bcrypt.generate_password_hash(default_pass).decode('utf-8')
		admin = User(uuid = uuid.uuid1().hex, phone = default_email, pwd = pwd, rights = "Super Admin")
		academics = Service(uuid = uuid.uuid1().hex, name = "Academics Module", description = "School Management")
		inventory = Service(uuid = uuid.uuid1().hex, name = "Inventory Module", description = "Stock Management")
		db.session.add_all([admin, academics, inventory])
		db.session.commit()
		print("System Initialised successfully!")
	else:
		print("System Already Initialised!")
