import os
import datetime
import json
import uuid

from geopy import distance
from datetime import timezone
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

class OutputLocation:
	def __init__(self, locationModel):
		self.uuid = locationModel.uuid
		self.latitude = locationModel.latitude
		self.longitude = locationModel.longitude
		self.timestamp = locationModel.timestamp
	
	def toJson(self):
		return json.dumps(self.__dict__)

	def __repr__(self):
		return self.toJson()


def obj_dict(obj):
    return obj.__dict__

class Location(db.Model):
	uuid = db.Column(db.String(32), unique=True, nullable=False, primary_key=True)
	latitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=False)
	longitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=False)
	timestamp = db.Column(db.Integer(), unique=False, nullable=False, primary_key=False)

	def __repr__(self):
		return self.timestamp

@app.route("/", methods=["GET", "POST"])
def home():
	return render_template("home.html")

@app.route('/locations')
def get_locations():
	arrayList = []

	results = Location.query.order_by(Location.timestamp).all()
	for i in range(len(results)):
		location = results[i]
		outLocation = OutputLocation(location)
		if (i == 0):
			outLocation.timeDelta = 0
			outLocation.spaceDelta = 0
		else:
			outLocation.timeDelta = (location.timestamp - results[i-1].timestamp) / 1000
			oldLL = (results[i-1].latitude, results[i-1].longitude)
			thisLL = (location.latitude, location.longitude)
			outLocation.spaceDelta = distance.distance(oldLL, thisLL).meters
		arrayList.append(outLocation)

	return json.dumps(arrayList, default=obj_dict)


@app.route('/new', methods=['POST'])
def add_new():
	content = request.get_json()
	print(content)
	if 'timestamp' not in content:
		content["timestamp"] = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000

	location = Location(latitude=content["latitude"], longitude=content["longitude"], timestamp=content["timestamp"], uuid=uuid.uuid1().hex)
	db.session.add(location)
	db.session.commit()
	return '', 204
