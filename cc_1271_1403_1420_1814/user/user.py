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



#----------------------------------------------------------------------------------------------------------------------#

#1) Add user (API)	 
@app.route('/api/v1/users',methods=["PUT","POST"])
def create_user():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	if(request.method!="PUT"):
		abort(405)
	user={
    	'username':request.get_json()['username'],
    	'password':request.get_json()['password'],
    	'type':'PUT',
    	'table':'user'
	}
	if not request.get_json() or not 'username' in request.get_json() or not 'password' in request.get_json():
		abort(400)
	if len(user['password'])<40 or not user['password'].isalnum() :
		abort(400)
	user=requests.post("http://52.207.112.21/api/v1/db/write",json=user)
	#return jsonify(user.json())
	if(str(user.json())=="1"):
		return jsonify(), 201
	if(str(user.json())=="0"):
		abort(400)

	
	

 
#2)Remove user (API)
@app.route("/api/v1/users/<username>",methods=["DELETE"])
def remove_user(username):
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	user={'username':username, 'type': 'DELETE', 'table':'user'}
	user=requests.post("http://52.207.112.21/api/v1/db/write",json=user)
	if(str(user.json())=="1"):
		return jsonify(), 200
	if(str(user.json())=="0"):
		abort(400)	


		
#10)List all users (API)
@app.route("/api/v1/users",methods=["GET"])
def list_all_users():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	print(data)
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	user={'table':"user"}
	new=requests.post("http://52.207.112.21/api/v1/db/read",json=user)
	if(str(new.json())=="0"):
		return jsonify(),204
	return jsonify(new.json()),200



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

