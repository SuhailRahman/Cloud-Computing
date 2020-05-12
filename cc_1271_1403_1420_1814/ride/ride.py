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



#class Ride(db.Model):
#	id = db.Column(db.Integer,primary_key=True)   
#	created_by= db.Column(db.String(50), nullable=False)
#	timestamp= db.Column(db.String(50))
#	source= db.Column(db.String(50))
#	destination= db.Column(db.String(50))
#	#users=db.relationship('Shared_user', backref="Ride", cascade="all, delete-orphan" , lazy='dynamic')
#	users=db.relationship('Shared_user',cascade="all, delete-orphan" , lazy='dynamic')


#class Shared_user(db.Model):
#	rideid = db.Column(db.Integer, db.ForeignKey('ride.id'),nullable=False,primary_key=True)
#	users=db.Column(db.String(100),nullable=False,primary_key=True)


#class SharedSchema(ma.ModelSchema):
#	class Meta:
#		model = Shared_user

#class RideSchema(ma.ModelSchema):
#	class Meta:
#		model = Ride

#ride_schema=RideSchema()
#rides_schema=RideSchema(many=True)

#shared_schema=SharedSchema()
#shareds_schema=SharedSchema(many=True)



#------------------------------------------------------------#


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
	#output=['suhail','riya','aish','neha','krits','yash','harsh','shivani']

	ride_username=request.get_json()['created_by']
	timestamp=request.get_json()['timestamp']
	source=request.get_json()['source']
	destination=request.get_json()['destination']

	if((int(source)<1 or int(source)>198) and (int(destination)<1 or int(destination)>198)):
		abort(400)
	riders={"created_by":ride_username,"timestamp":timestamp,"source":source,"destination":destination, "table":"ride", "id":"1"}
	#return jsonify(output)
	if(bool(riders['created_by'] in output)):
		created=requests.post("http://52.207.112.21/api/v1/db/write",json=riders)
		# created=requests.post("http://34.237.219.94/api/v1/db/write",json=riders)
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
	#if(int(source)<1 or int(source)>198) and (int(destination)<1 or int(destination)>198):
	#	abort(400)
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
	#output=['suhail','riya','aish','rithvik','shivani']
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
