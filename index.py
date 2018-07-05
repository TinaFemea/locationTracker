import os
import datetime
import json
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
    latitude = db.Column(db.String(80), unique=False, nullable=False, primary_key=True)
    longitude = db.Column(db.String(80), unique=False, nullable=False, primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=False, nullable=False, primary_key=True, default=datetime.datetime.utcnow())

    def __repr__(self):
        return self.toJSON

    def toJSON(self):
    	return json.dumps(self.__dict__)


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

	location = Location(latitude=content["latitude"], longitude=content["longitude"], timestamp=content["timestamp"])
	db.session.add(location)
	db.session.commit()
	return '', 204
