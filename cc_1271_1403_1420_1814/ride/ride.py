from flask import Flask,request,jsonify,redirect, url_for, abort
import os
from sqlalchemy import desc
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema
from datetime import datetime
import requests
import json
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)



#---------------------------------------------------------------------------------------------------------------#


#3)Create a new ride 
@app.route("/api/v1/rides",methods=["POST","PUT"])
def create_ride():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	if(request.method!="POST"):
		abort(405)
	user=requests.get("http://load-balancer-570133840.us-east-1.elb.amazonaws.com/api/v1/users",headers={"Origin":"http://54.157.52.201"})
	output=user.json()

	ride_username=request.get_json()['created_by']
	timestamp=request.get_json()['timestamp']
	source=request.get_json()['source']
	destination=request.get_json()['destination']

	if((int(source)<1 or int(source)>198) and (int(destination)<1 or int(destination)>198)):
		abort(400)
	riders={"created_by":ride_username,"timestamp":timestamp,"source":source,"destination":destination, "table":"ride", "id":"1"}
	if(bool(riders['created_by'] in output)):
		created=requests.post("http://52.207.112.21/api/v1/db/write",json=riders)
		if(str(created.json())=="1"):
			return jsonify(),201
	abort(400)

#4)List all upcoming rides for a given source and destination
@app.route('/api/v1/rides')
def all_rides():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	source = request.args.get('source')
	destination = request.args.get('destination')
	if(int(source)==int(destination)):
		abort(400)
	if(len(source)==0 or len(destination)==0):
		abort(400)
	ride={'source':source, 'destination':destination , 'table':'ride' , 'id' : "2"}
	ride=requests.post("http://52.207.112.21/api/v1/db/read",json=ride)
	if(str(ride.json())=="0"):
		return jsonify(),204
	if(str(ride.json())=="1"):
		abort(400)
	return jsonify(ride.json()),200
	

#5) List all the details of a given ride 
@app.route("/api/v1/rides/<rideid>")
def ride_details(rideid):
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	ride={'rideid':rideid, 'table':'ride','id': "1" }
	ride=requests.post("http://52.207.112.21/api/v1/db/read",json=ride)
	if(str(ride.json())=="0"):
		return jsonify(),204
	return jsonify(ride.json()),200	


#6)Join an existing ride (API)
@app.route("/api/v1/rides/<rideid>",methods=["POST"])
def join_ride(rideid):
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	if not request.get_json() or not 'username' in request.get_json(): 
		abort(400)
	username=request.get_json()["username"]
	user=requests.get("http://load-balancer-570133840.us-east-1.elb.amazonaws.com/api/v1/users",headers={"Origin":"http://54.157.52.201"})
	output=user.json()
	ride={'rideid':rideid,'username':username,'table':'ride', 'id':"2",'output':output}
	ride=requests.post("http://52.207.112.21/api/v1/db/write",json=ride) 
	if(str(ride.json())=="0"):
		abort(400)
	if(str(ride.json())=="1"):
		return jsonify(),200
	if(str(ride.json())=="2"):
		return jsonify(),204


#7)Delete ride (API)
@app.route("/api/v1/rides/<rideid>",methods=["DELETE"])
def remove_ride(rideid):
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	ride={'rideid':rideid,'table':'ride','id':"3"}
	ride=requests.post("http://52.207.112.21/api/v1/db/write",json=ride)
	if(str(ride.json())=="0"):
		abort(400)
	if(str(ride.json())=="1"):
		return jsonify(),200


#12)Number of rides
@app.route("/api/v1/rides/count")
def no_of_rides():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	ride={'table':'ride','id':"3"}
	ride=requests.post("http://52.207.112.21/api/v1/db/read",json=ride)
	return jsonify(ride.json()),200


#11)Clear Database (API)
@app.route("/api/v1/db/clear",methods=["POST"])
def clear_data():
	with open('count.json') as f:
		data=json.load(f)
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	clear={'table':'clear'}
	clear=requests.post("http://52.207.112.21/api/v1/db/write",json=clear)
	return jsonify(),200


#13)Get total HTTP requests made to microservice
@app.route("/api/v1/_count")
def total():
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	with open('count.json') as f:
		data=json.load(f)
	x=data["count"]
	l=[]
	l.append(x)
	return jsonify(l),200

#14)Reset HTTP requests counter
@app.route("/api/v1/_count",methods=["DELETE"])
def reset():
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	with open('count.json') as f:
		data=json.load(f)
	data["count"]=0
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	return jsonify(),200


if __name__ == '__main__':	
	app.run(host='0.0.0.0',debug=True,port=80)



