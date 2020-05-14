from flask import Flask,request,jsonify,redirect, url_for, abort
import os
from sqlalchemy import desc
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema
from datetime import datetime
import requests
import json
import pandas as pd
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///db.sqlite3'
db = SQLAlchemy(app)
ma=Marshmallow(app)
data=pd.read_csv("AreaNameEnum.csv")


class User(db.Model):
    username = db.Column(db.String(50),primary_key=True)
    password = db.Column(db.String(50))
	
	

class UserSchema(ma.ModelSchema):
	class Meta:
		model = User

	
user_schema=UserSchema()
users_schema=UserSchema(many=True)



#------------------------------------------------------------#
#WRITING AND READING TO DATABASE

#User
@app.route('/api/v1/write/user' , methods=["POST"])
def write():	
	username=request.get_json()['username']
	password=request.get_json()['password']
	user= User(username=username,password=password)
	db.session.add(user)
	db.session.commit()
	return ""

@app.route('/api/v1/read/user')
def read():
	user =  User.query.all()
	output=user
	user_schema=UserSchema(many=True)
	output=user_schema.dump(user)
	return jsonify(output)

#------------------------------------------------------------#



#------------------------------------------------------------#

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
    	'password':request.get_json()['password']
	}
	if not request.get_json() or not 'username' in request.get_json() or not 'password' in request.get_json():
		abort(400)
	if len(user['password'])<40 or not user['password'].isalnum() :
		abort(400)
	
	if(bool(User.query.filter_by(username=user["username"]).first())):
			abort(400,"username already exists")
	user_request=requests.post("52.206.225.55/api/v1/write/user",json=user)
	user_request.text
	return jsonify(),201

 
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
	users=User.query.filter_by(username=username).first()
	if users:
		db.session.delete(users)	
		db.session.commit()
		return jsonify(),200
	abort(400)



#10)List all users (API)
@app.route("/api/v1/users",methods=["GET"])
def list_all_users():
	with open('count.json') as f:
		data=json.load(f)
	data["count"]+=1
	with open('count.json','w') as json_file:
		json.dump(data,json_file)
	with app.test_client() as client:
		response = client.get('/')
		if(response.status_code==405):
			abort (str(response.status_code))
	users=User.query.all()
	user_schema=UserSchema(many=True)
	output=user_schema.dump(users)
	new=[]
	for i in output:
		new.append(i["username"])
	if(len(new)!=0):
		return jsonify(new),200
	return jsonify(),204

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
	meta=db.metadata
	for table in reversed(meta.sorted_tables):
		db.session.execute(table.delete())
	db.session.commit()
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

#{"created_by":"suhail","timestamp":"31-05-2021:23-16-10","source":"3","destination":"5"}
#{"username":"Karan","password":"dasdasdasdwjejqkhejkdasdasdaqwhjkeqhjkwe3344"}
