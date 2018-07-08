import os
import datetime
import json
import uuid

from geopy import distance
from datetime import timezone
from collections import OrderedDict
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, DDL
from sqlalchemy.event import listen

app = Flask(__name__,
			static_url_path='', 
			static_folder='static',
			template_folder='static/templates')


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "locations.db"))

startLocation = (0, 0)

app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class OutputLocation:
	def __init__(self, locationModel):
		self.uuid = locationModel.uuid
		self.latitude = locationModel.latitude
		self.longitude = locationModel.longitude
		self.timestamp = locationModel.timestamp
		self.startDelta = locationModel.startDelta
		self.timeDelta = locationModel.timeDelta
		self.lap = locationModel.lap
		self.movingCloser = locationModel.movingCloser
	
	def toJson(self):
		return json.dumps(self.__dict__)

	def __repr__(self):
		return self.toJson()

def obj_dict(obj):
	return obj.__dict__

class StartingPoint(db.Model):
	latitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=True)
	longitude = db.Column(db.Float(), unique=False, nullable=False, primary_key=True)
	timestamp = db.Column(db.Float(), unique=False, nullable=False, primary_key=True)

	def __repr__(self):
		return self.timestamp

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
	timestamp = db.Column(db.Float(), unique=False, nullable=False, primary_key=False)
	startDelta = db.Column(db.Float(), unique=False, nullable=False, primary_key=False) 
	spaceDelta = db.Column(db.Float(), unique=False, nullable=True, primary_key=False) 
	timeDelta = db.Column(db.Float(), unique=False, nullable=True, primary_key=False) 
	lap = db.Column(db.Integer(), unique=False, nullable=True, primary_key=False) 
	movingCloser = db.Column(db.Boolean(), unique=False, nullable=True, primary_key=False)

	def __repr__(self):
		return self.toJSON

	def toJSON(self):
		return json.dumps(self.__dict__)

def afterCreate(target, connection, **kw):
	connection.execute("Insert into starting_point (latitude, longitude, timestamp) values (54.083245, -4.744232, 0)")

event.listen(StartingPoint.__table__, "after_create", afterCreate)


@app.before_first_request
def beforeFirst():
	global startLocation
	
	firstPoint = StartingPoint.query.order_by(StartingPoint.timestamp.desc()).first()
	startLocation = (firstPoint.latitude, firstPoint.longitude)

@app.route("/", methods=["GET", "POST"])
def home():
	timestamps = db.session.query(Location.timestamp).all()
	dayList = []
	for timestamp in timestamps:
		dayString = getDayFromTS(timestamp.timestamp)
		if (dayString not in dayList):
			dayList.append(dayString)

	return render_template("home.html", days = dayList)

@app.route('/locations')
def get_locations():
	filterTS = request.args.get('after', default = 0, type = int)
	filterLap = request.args.get('filterLap')
	filterDate = request.args.get('filterDate')

	query = Location.query.filter(Location.timestamp > filterTS)
	
	if (filterDate == None):
		filterDate = datetime.date.today().isoformat()

	if(filterDate is not "all"):
		startEndTime = getRangefromDay(filterDate)
		print(startEndTime)
		query = query.filter(Location.timestamp >= startEndTime[0]).filter(Location.timestamp <= startEndTime[1])


	if (filterLap is not None and filterLap != "All"):
		print(filterLap)
		query = query.filter(Location.lap == filterLap)

	results = query.order_by(Location.timestamp).all()

	retValue = {}
	retValue["results"] = results
	retValue["startPoint"] = startLocation
	return jsonify(retValue)

def getLastPointFromDB():
	return Location.query.order_by(Location.timestamp.desc()).first()

def getDayFromTS(timestamp):
	theDT = datetime.datetime.utcfromtimestamp(timestamp/1000)
	return datetime.date(theDT.year, theDT.month, theDT.day).isoformat();

def getRangefromDay(dayString):
	startDT = datetime.datetime.strptime( dayString, "%Y-%m-%d" );
	startJTS = startDT.replace(tzinfo=timezone.utc).timestamp() * 1000
	endDT = startDT + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
	endJTS = endDT.replace(tzinfo=timezone.utc).timestamp() * 1000
	return (startJTS, endJTS)

def computeLap(currPoint, prevPoint):
	if (getDayFromTS(currPoint.timestamp) != getDayFromTS(prevPoint.timestamp)): # date changed
		return 0

	if ((currPoint.timestamp - prevPoint.timestamp) > (3600 * 1000)): # one hour
		return prevPoint.lap + 1

	if (currPoint.startDelta > 50): # we're really far away
		return prevPoint.lap

	if (currPoint.startDelta == prevPoint.startDelta): # we haven't moved
		return prevPoint.lap
	
	if (prevPoint.movingCloser == True and currPoint.movingCloser == False): #we've changed directions
		return prevPoint.lap + 1

	return prevPoint.lap

@app.route('/new', methods=['POST'])
def add_new():
	content = request.get_json()
	if 'timestamp' not in content:
		content["timestamp"] = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000

	content["timestamp"] = float(content["timestamp"])
	content["latitude"] = float(content["latitude"])
	content["longitude"] = float(content["longitude"])

	location = Location(latitude=content["latitude"], 
						longitude=content["longitude"], 
						timestamp=content["timestamp"], 
						uuid=uuid.uuid1().hex)

	thisLL = (content["latitude"], content["longitude"])
	location.startDelta = distance.distance(thisLL, startLocation).meters

	prevPoint = getLastPointFromDB()
	if (prevPoint is None):
		location.spaceDelta = 0
		location.timeDelta = 0
		location.lap = 0
		location.movingCloser = False
	else:
		if (prevPoint.latitude == location.latitude and prevPoint.longitude == location.longitude):
			print ("dupe")
			return '', 204
		oldLL = (prevPoint.latitude, prevPoint.longitude)
		location.spaceDelta = distance.distance(oldLL, thisLL).meters
		location.timeDelta = (location.timestamp - prevPoint.timestamp) / 1000
		location.movingCloser = (location.startDelta < prevPoint.startDelta)
		location.lap = computeLap(location, prevPoint)

	db.session.add(location)
	db.session.commit()
	return '', 204

@app.route('/startPoint', methods=['POST'])
def add_startPoint():
	global startLocation

	content = request.get_json()
	if 'timestamp' not in content:
		content["timestamp"] = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000
	startLocation = (content["latitude"], content["longitude"])
	startPoint = StartingPoint(latitude=content["latitude"], longitude=content["longitude"], timestamp=content["timestamp"])
	db.session.add(startPoint)
	db.session.commit()
	return '', 204