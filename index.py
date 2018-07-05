import os
import datetime
import json
import uuid

from collections import OrderedDict
from flask import Flask, jsonify, request, render_template

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__,
			static_url_path='', 
			static_folder='static',
			template_folder='static/templates')


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "locations.db"))

app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DictSerializable(object):
	def _asdict(self):
		result = OrderedDict()
		for key in self.__mapper__.c.keys():
			result[key] = getattr(self, key)
		return result

class Location(db.Model, DictSerializable):
	uuid = db.Column(db.String(32), unique=True, nullable=False, primary_key=True)
	latitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=False)
	longitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=False)
	timestamp = db.Column(db.DateTime(), unique=False, nullable=False, primary_key=False)

	def __repr__(self):
		return self.toJSON

	def toJSON(self):
		return json.dumps(self.__dict__)

def convert_java_millis(java_time_millis):
	# Provided a java timestamp convert it into python date time object
	ds = datetime.datetime.fromtimestamp(
		int(str(java_time_millis)[:10])) if java_time_millis else None
	ds = ds.replace(hour=ds.hour,minute=ds.minute,second=ds.second,microsecond=int(str(java_time_millis)[10:]) * 1000)
	return ds	

@app.route("/", methods=["GET", "POST"])
def home():
	if request.form:
		location = Location(latitude=request.form.get("latitude"), longitude=request.form.get("longitude"))
		db.session.add(location)
		db.session.commit()

	locations = Location.query.all()
	return render_template("home.html", locations=locations)

@app.route('/locations')
def get_locations():
	locations = Location.query.all()
	return jsonify(locations)


@app.route('/new', methods=['POST'])
def add_new():
	content = request.get_json()
	print(content)
	if 'timestamp' not in content:
		content["timestamp"] = datetime.datetime.utcnow()
	else:
		content["timestamp"] = convert_java_millis(content["timestamp"])

	location = Location(latitude=content["latitude"], longitude=content["longitude"], timestamp=content["timestamp"], uuid=uuid.uuid1().hex)
	db.session.add(location)
	db.session.commit()
	return '', 204
