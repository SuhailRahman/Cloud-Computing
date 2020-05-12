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

#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///db.sqlite3'
#db = SQLAlchemy(app)
#ma=Marshmallow(app)



#class User(db.Model):
#    username = db.Column(db.String(50),primary_key=True)
#    password = db.Column(db.String(50))
	
	

#class UserSchema(ma.ModelSchema):
#	class Meta:
#		model = User

	
#user_schema=UserSchema()
#users_schema=UserSchema(many=True)



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

#Reading the database
@app.route("/api/v1/db/read",methods=["POST"])
def read():


	# with open('count.json') as f:
	# 	data=json.load(f)
	# data["read_count"]+=1
	# with open('count.json','w') as json_file:
	# 	json.dump(data,json_file)


	data=request.get_json()
	table=data['table']

	#Read users
	if(table=="user"):
		users=User.query.all()
		user_schema=UserSchema(many=True)
		output=user_schema.dump(users)
		new=[]
		for i in output:
			new.append(i["username"])
		if(len(new)!=0):
			return jsonify(new)
		return "0"

	#Read rides
	if(table=="ride"):

		id = data['id']

		if(id==1):
			rideid=data['rideid']
			det_ride=Ride.query.filter_by(id=rideid)
			if (bool(Ride.query.filter_by(id=rideid).first())):
				ride_schema=RideSchema(many=True)
				output=ride_schema.dump(det_ride)
				st=[]
				for i in output:
					for j in i["users"]:
						st.append(j["users"])
					i["users"]=st
					i.pop("id")
					i["rideId"]=rideid
					x=i["created_by"]
					i.pop("created_by")
					i["Created_by"]=x
					y=i["timestamp"]
					i.pop("timestamp")
					i["Timestamp"]=y
				if(len(output)!=0):
					return jsonify(output)
			return "0"

		if(id==2):
			ride=[]
			flag=False
			source=data['source']
			destination=data['destination']
			upcoming=Ride.query.filter_by(source=source,destination=destination).all()
			ride_schema=RideSchema(many=True)
			output=ride_schema.dump(upcoming)
			for details in output:
				d={}
				d.update(details)
				d.pop("source")
				d.pop("destination")
				d.pop("users")
				x=d["id"]
				y=d["created_by"]
				d.pop("created_by")
				d.pop("id")
				d["rideId"]=x
				d["username"]=y
				timestamp=d["timestamp"]
				date_time=timestamp.split(":")
				s_m_h=date_time[1].split("-")
				d_m_y=date_time[0].split("-")
				new_date=d_m_y[2]+"-"+d_m_y[1]+"-"+d_m_y[0]+" "+s_m_h[2]+":"+s_m_h[1]+":"+s_m_h[0]
				current=datetime.now()				
				date1 = datetime.strptime(new_date, '%Y-%m-%d %H:%M:%S')
				if(date1>current):
					ride.append(d)
					flag=True
			if(not flag):
				return "0"
			return jsonify(ride)

		if(id==3):
			x=Ride.query.count()
			l=[]
			l.append(x)
			return jsonify(l)


#Writing to db
@app.route("/api/v1/db/write",methods=["POST"])
def write():


	# with open('count.json') as f:
	# 	data=json.load(f)
	# data["write_count"]+=1
	# with open('count.json','w') as json_file:
	# 	json.dump(data,json_file)


	data=request.get_json()
	table=data['table']

	#Add user
	if(table=="user"):
		method=data['type']
		if(method=="PUT"):
			username=data['username']
			password=data['password']
			if(bool(User.query.filter_by(username=data["username"]).first())):
				return "0"
			#user_request=requests.post("http://52.206.225.55/api/v1/write/user",json=user)
			create_user=User(username=username,password=password)
			db.session.add(create_user)
			db.session.commit()
			return "1"

		#Remove user
		elif(method=='DELETE'):
			username=data['username']
			users=User.query.filter_by(username=username).first()
			if users:
				db.session.delete(users)	
				db.session.commit()
				return "1"
			return "0"


	#Add rides		
	if(table=="ride"):

		id = data['id']

		#Creating rides
		if(id==1):
			created_by=data['created_by']
			timestamp=data['timestamp']
			source=data['source']
			destination=data['destination']
			ride= Ride(created_by=created_by,timestamp=timestamp,source=source,destination=destination)
			db.session.add(ride)
			db.session.commit()
			return "1"
		
		#Join an existing ride
		if(id==2):
			rideid=data['rideid']
			username=data['username']
			output=data['output']
			ride=Ride.query.filter_by(id=rideid).first()
			if bool(username in output):
				if bool(ride):
					if(Ride.query.filter_by(created_by=username,id=rideid).first()):
						return "0"
					if(Shared_user.query.filter_by(rideid=rideid,users=username)).first():
						return "0"
					shared= Shared_user(rideid=rideid,users=username)
					db.session.add(shared)
					db.session.commit()
					return "1"
				return "2"
			return "2"

		#Deleting a ride
		if(id==3):
			rideid=data['rideid']
			rides=Ride.query.filter_by(id=rideid).first()
			if rides:
				db.session.delete(rides)	
				db.session.commit()
				return "1"
			return "0"


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
	# meta=db.metadata
	# for table in reversed(meta.sorted_tables):
	# 	db.session.execute(table.delete())
	# db.session.commit()
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

#{"created_by":"suhail","timestamp":"31-05-2021:23-16-10","source":"3","destination":"5"}
#{"username":"Karan","password":"dasdasdasdwjejqkhejkdasdasdaqwhjkeqhjkwe3344"}
