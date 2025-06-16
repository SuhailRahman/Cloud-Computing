from flask import Flask,request,jsonify,redirect, url_for, abort
import os
from sqlalchemy import desc
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema
from datetime import datetime
import requests
import json
from flask_sqlalchemy import SQLAlchemy
import pika
import sqlite3
import threading
import ast
import sys
import time
import docker
import subprocess
from kazoo.client import KazooClient
from kazoo.client import KazooState
import logging

logging.basicConfig()

zk= KazooClient(hosts='zoo:2181')
zk.start()


client = docker.DockerClient(base_url='unix://var/run/docker.sock')
x=client.containers.list()
print(x)
proc = subprocess.Popen(["docker inspect -f '{{.State.Pid}}' "+x[0].id], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
print(out.decode("utf-8"))
pid_of_container=out.decode("utf-8")

#Creating Ephemeral Nodes for each worker
zk.create("/orchestrator/"+pid_of_container.strip(),b'0',ephemeral=True)
data,stat=zk.get('/orchestrator/'+pid_of_container.strip())
print("version %s ,data: %s" % (stat.version,data.decode('utf-8')))

time.sleep(1)

my_mutex = threading.Lock()

app = Flask(__name__)

#----------------------------------------------------------------------------------------------------------------------------

if(sys.argv[1]=="master"):

	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///db.sqlite3'
	db = SQLAlchemy(app)
	ma=Marshmallow(app)


	class User(db.Model):
	    username = db.Column(db.String(50),primary_key=True)
	    password = db.Column(db.String(50))

	class UserSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = User

	user_schema=UserSchema()
	users_schema=UserSchema(many=True)



	class Ride(db.Model):
		id = db.Column(db.Integer,primary_key=True)   
		created_by= db.Column(db.String(50), nullable=False)
		timestamp= db.Column(db.String(50))
		source= db.Column(db.String(50))
		destination= db.Column(db.String(50))
		users=db.relationship('Shared_user',cascade="all, delete-orphan" , lazy='dynamic')


	class Shared_user(db.Model):
		rideid = db.Column(db.Integer, db.ForeignKey('ride.id'),nullable=False,primary_key=True)
		users=db.Column(db.String(100),nullable=False,primary_key=True)


	class SharedSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = Shared_user

	class RideSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = Ride

	ride_schema=RideSchema()
	rides_schema=RideSchema(many=True)

	shared_schema=SharedSchema()
	shareds_schema=SharedSchema(many=True)

	db.create_all() #Creates a database if it doesn't exist

	def callback_write(ch, method, properties, body):
		message=body.decode("utf-8")
		sql=message.split(";")

		if(sql[0]=="clear"):
			meta=db.metadata
			for table in reversed(meta.sorted_tables):
				db.session.execute(table.delete())
			db.session.commit()
			master_sync(message) #calling sync function
			print("deleted master")

		#User table
		if(sql[0]=="user"):
			print(sql[0],sql[1],sql[2])
			#Add User
			if(sql[1]=="PUT"):
				username=sql[2]
				password=sql[3]
				exist=db.session.query(db.session.query(User).filter_by(username=sql[2]).exists() ).scalar()
				if(not bool(exist)):
					create_user=User(username=username,password=password)
					db.session.add(create_user)
					db.session.commit()
				master_sync(message) #calling sync function
				users=User.query.all()
				user_schema=UserSchema(many=True)
				output=user_schema.dump(users)
				print(output)

			#Remove User
			if(sql[1]=="DELETE"):
				username=sql[2]
				users=User.query.filter_by(username=username).first()
				#if user is existing
				if users:
					db.session.delete(users)	
					db.session.commit()
				master_sync(message) #calling sync function
				users=User.query.all()
				user_schema=UserSchema(many=True)
				output=user_schema.dump(users)
				print(output)

		#Ride Table
		if(sql[0]=="ride"):
			#Create a New Ride
			if(sql[1]=="1"):
				print("create new ride"," ",sql[0]," ",sql[1]," ",sql[2]," ",sql[3]," ",sql[4]," ",sql[5])
				created_by=sql[2]
				timestamp=sql[3]
				source=sql[4]
				destination=sql[5]
				ride= Ride(created_by=created_by,timestamp=timestamp,source=source,destination=destination)
				db.session.add(ride)
				db.session.commit()
				master_sync(message) #calling sync function
				ride=Ride.query.all()
				ride_schema=RideSchema(many=True)
				output=ride_schema.dump(ride)
				print(output)

			#Join a Ride
			if(sql[1]=="2"):
				print("join a ride",sql[0],sql[1],sql[2],sql[3])
				rideid=sql[2]
				username=sql[3]
				ride=Ride.query.filter_by(id=rideid).first()
				#if a ride is existing
				if bool(ride):
					shared= Shared_user(rideid=rideid,users=username)
					db.session.add(shared)
					db.session.commit()
				master_sync(message) #calling sync function
				ride=Ride.query.all()
				ride_schema=RideSchema(many=True)
				output=ride_schema.dump(ride)
				print(output)

			#Delete a Ride
			if(sql[1]=="3"):
				print("delete ride",sql[0],sql[1],sql[2])
				rideid=sql[2]
				rides=Ride.query.filter_by(id=rideid).first()
				#if a ride is existing
				if rides:
					db.session.delete(rides)	
					db.session.commit()
				master_sync(message) #calling sync function
				ride=Ride.query.all()
				ride_schema=RideSchema(many=True)
				output=ride_schema.dump(ride)
				print(output)

		print(" [x] Done")
		ch.basic_ack(delivery_tag=method.delivery_tag)


	#Writing into Master Database
	def write():
		connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
		channel = connection.channel()
		channel.queue_declare(queue='write_queue', durable=True)
		print(' [*] Waiting for messages.')
		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(queue='write_queue', on_message_callback=callback_write)
		channel.start_consuming()

	#Making a Connection With Sync Queue
	def master_sync(message):
		connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
		channel = connection.channel()
		channel.exchange_declare(exchange='logs', exchange_type='fanout')
		channel.basic_publish(exchange='logs', routing_key='', body=message, properties=pika.BasicProperties(delivery_mode=2,))
		print(" [x] Sent %r" % message)
		connection.close()

	write()

if(sys.argv[1]=="slave"):


	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

	with open('slave/count1.json') as f:
		data=json.load(f)
	count=int(data["count"])
	a=data["count"]
	print(type(count))
	print("database name",a)
	a=str(a)
	a="sqlite:///new"+a+".sqlite3"

	app.config['SQLALCHEMY_DATABASE_URI'] =a

	db = SQLAlchemy(app)
	ma=Marshmallow(app)

	class User(db.Model):
	    username = db.Column(db.String(50),primary_key=True)
	    password = db.Column(db.String(50))

	class UserSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = User

	user_schema=UserSchema()
	users_schema=UserSchema(many=True)



	class Ride(db.Model):
		id = db.Column(db.Integer,primary_key=True)   
		created_by= db.Column(db.String(50), nullable=False)
		timestamp= db.Column(db.String(50))
		source= db.Column(db.String(50))
		destination= db.Column(db.String(50))
		users=db.relationship('Shared_user',cascade="all, delete-orphan" , lazy='dynamic')


	class Shared_user(db.Model):
		rideid = db.Column(db.Integer, db.ForeignKey('ride.id'),nullable=False,primary_key=True)
		users=db.Column(db.String(100),nullable=False,primary_key=True)


	class SharedSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = Shared_user

	class RideSchema(ma.SQLAlchemyAutoSchema):
		class Meta:
			model = Ride

	ride_schema=RideSchema()
	rides_schema=RideSchema(many=True)

	shared_schema=SharedSchema()
	shareds_schema=SharedSchema(many=True)


	db.create_all() #Creates a database if it doesn't exist

	#Data replication ,copying the contents of master database into the newly spawned slave
	if(count > 1):

		sqliteConnection = sqlite3.connect('slave/db.sqlite3')
		cursor = sqliteConnection.cursor()
		print("Database created and Successfully Connected to SQLite")

		user = """SELECT * from User"""
		cursor.execute(user)
		records = cursor.fetchall()
		for i in range(len(records)):
			print("USER: ",records[i][0],records[i][1])
			username=records[i][0]
			password=records[i][1]
			create_user=User(username=username,password=password)
			db.session.add(create_user)
			db.session.commit()

		users=User.query.all()
		user_schema=UserSchema(many=True)
		output=user_schema.dump(users)
		print("USERS-----",output)

		ride = """SELECT * from Ride"""
		cursor.execute(ride)
		records = cursor.fetchall()
		for i in range(len(records)):
			print("RIDE",records[i][1],records[i][2],records[i][3],records[i][4])
			created_by=records[i][1]
			timestamp=records[i][2]
			source=records[i][3]
			destination=records[i][4]
			create_ride=Ride(created_by=created_by,timestamp=timestamp,source=source,destination=destination)
			db.session.add(create_ride)
			db.session.commit()

		ride=Ride.query.all()
		ride_schema=RideSchema(many=True)
		output=ride_schema.dump(ride)
		print("RIDES----",output)

		shared_user = """SELECT * from Shared_user"""
		cursor.execute(shared_user)
		records = cursor.fetchall()
		for i in range(len(records)):
			print("SHARED_USER",records[i][0],records[i][1])
			rideid=records[i][0]
			username=records[i][1]
			shared_user=Shared_user(rideid=rideid,users=username)
			db.session.add(shared_user)
			db.session.commit()

		Shared=Shared_user.query.all()
		shared_user=SharedSchema(many=True)
		output=shared_user.dump(Shared)
		print("Shared_users----",output)

		cursor.close()

	#Reading operation for slaves
	class thread_two(threading.Thread):
		def run(self):
			global my_mutex
			print ("Reading operation is happening...")
			def db_read(n):
				global my_mutex
				sql=n.split(";") #splitting the message on semi colon
				#List All Users
				if(sql[0]=="user"):
					my_mutex.acquire() #lock acquired
					users=User.query.all()
					user_schema=UserSchema(many=True)
					output=user_schema.dump(users)
					my_mutex.release() #lock released
					new=[]
					for i in output:
						new.append(i["username"])
					ini_list=new
					string=str(ini_list)
					return string	
					
				#Rides	
				if(sql[0]=="ride"):
					#List all the details of a given ride 
					if(sql[1]=="1"):
						rideid=sql[2]
						my_mutex.acquire() #lock acquired
						det_ride=Ride.query.filter_by(id=rideid)
						if (bool(Ride.query.filter_by(id=rideid).first())):
							ride_schema=RideSchema(many=True)
							output=ride_schema.dump(det_ride)
							st=[]
							for i in output:
								print(i)
								u=Shared_user.query.filter_by(rideid=rideid)
								shareds_schema=SharedSchema(many=True)
								u_out=shareds_schema.dump(u)
								print(u_out)
								for j in u_out:
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
							string=str(output)
							my_mutex.release() #lock released
							return string
						my_mutex.release() #lock released
						return "0"

					#List all upcoming rides for a given source and destination
					if(sql[1]=="2"):
						source=sql[2]
						destination=sql[3]
						my_mutex.acquire() #lock acquired
						upcoming=Ride.query.filter_by(source=source,destination=destination).all()
						ride_schema=RideSchema(many=True)
						output=ride_schema.dump(upcoming)
						my_mutex.release() #lock released
						string=str(output)
						return string

					#Number of rides
					if(sql[1]=="3"):
						my_mutex.acquire()
						x=Ride.query.count()
						my_mutex.release()
						string=str(x)
						return string


			def on_request(ch, method, props, body):
				body=body.decode("utf-8")
				n= str(body)
				print(" [.] read statement(%s)" % n)
				response = db_read(n)	
				ch.basic_publish(exchange='',
				                 routing_key=props.reply_to,
				                 properties=pika.BasicProperties(correlation_id = \
				                                                     props.correlation_id),
				                 body=str(response))
				ch.basic_ack(delivery_tag=method.delivery_tag)


			#To make a connection with read queue
			def read():
				connection = pika.BlockingConnection(
			    pika.ConnectionParameters(host='rmq'))
				channel = connection.channel()
				channel.queue_declare(queue='read_queue')
				channel.basic_qos(prefetch_count=1) #Round robin operation
				channel.basic_consume(queue='read_queue', on_message_callback=on_request)
				print(" [x] Awaiting RPC requests")
				channel.start_consuming()

			read()

	#Sync Operation for Slaves
	class thread_one(threading.Thread):
		def run(self):
			global my_mutex
			print ("Syncing operation happening...")
			def callback(ch, method, properties, body):
				global my_mutex
				message=body.decode("utf-8")
				sql=message.split(";")
				print("entering callback..")
				#Database Clear
				if(sql[0]=="clear"):
					my_mutex.acquire()
					meta=db.metadata
					for table in reversed(meta.sorted_tables):
						db.session.execute(table.delete())
					db.session.commit()
					print("deleted1")
					my_mutex.release()

				#User Table
				if(sql[0]=="user"):
					print(sql[0],sql[1],sql[2])
					#Adding a User
					if(sql[1]=="PUT"):
						username=sql[2]
						password=sql[3]
						my_mutex.acquire()
						exist=db.session.query(db.session.query(User).filter_by(username=sql[2]).exists() ).scalar()
						if(not bool(exist)):
							create_user=User(username=username,password=password)
							db.session.add(create_user)
							db.session.commit()
						users=User.query.all()
						user_schema=UserSchema(many=True)
						output=user_schema.dump(users)
						print(output)
						my_mutex.release()

					#Removing a User
					if(sql[1]=="DELETE"):
						username=sql[2]
						my_mutex.acquire()
						users=User.query.filter_by(username=username).first()
						#If user doesn't exists then it adds into database
						if users:
							db.session.delete(users)	
							db.session.commit()
						users=User.query.all()
						user_schema=UserSchema(many=True)
						output=user_schema.dump(users)
						print(output)
						my_mutex.release()

				#Ride table
				if(sql[0]=="ride"):
					#Creating a new Ride
					if(sql[1]=="1"):
						print("create new ride"," ",sql[0]," ",sql[1]," ",sql[2]," ",sql[3]," ",sql[4]," ",sql[5])
						created_by=sql[2]
						timestamp=sql[3]
						source=sql[4]
						destination=sql[5]
						my_mutex.acquire()
						ride= Ride(created_by=created_by,timestamp=timestamp,source=source,destination=destination)
						db.session.add(ride)
						db.session.commit()
						ride=Ride.query.all()
						ride_schema=RideSchema(many=True)
						output=ride_schema.dump(ride)
						print(output)
						my_mutex.release()

					#Joining a ride
					if(sql[1]=="2"):
						print("join a ride",sql[0],sql[1],sql[2],sql[3])
						rideid=sql[2]
						username=sql[3]
						my_mutex.acquire()
						ride=Ride.query.filter_by(id=rideid).first()
						#if a ride is existing
						if bool(ride):
							shared= Shared_user(rideid=rideid,users=username)
							db.session.add(shared)
							db.session.commit()
						ride=Ride.query.all()
						ride_schema=RideSchema(many=True)
						output=ride_schema.dump(ride)
						print(output)
						my_mutex.release()
					
					#Deleting a Ride	
					if(sql[1]=="3"):
						print("delete ride",sql[0],sql[1],sql[2])
						rideid=sql[2]
						my_mutex.acquire()
						rides=Ride.query.filter_by(id=rideid).first()
						#if a ride is existing
						if rides:
							db.session.delete(rides)	
							db.session.commit()
						ride=Ride.query.all()
						ride_schema=RideSchema(many=True)
						output=ride_schema.dump(ride)
						print(output)
						my_mutex.release()
				print(" [x] Done")
				ch.basic_ack(delivery_tag=method.delivery_tag)

			def slave_sync():
				connection = pika.BlockingConnection(
				pika.ConnectionParameters(host='rmq'))
				channel = connection.channel()
				channel.exchange_declare(exchange='logs', exchange_type='fanout')
				result = channel.queue_declare(queue='', exclusive=True)
				queue_name = result.method.queue
				channel.queue_bind(exchange='logs', queue=queue_name)
				print(' [*] Updating the slave database.')
				channel.basic_qos(prefetch_count=1)
				channel.basic_consume(queue=queue_name, on_message_callback=callback)
				channel.start_consuming()
			print("Before slave_slave")
			slave_sync()
	t1 = thread_one() #Sync operation
	t2 = thread_two() #Reading operation
	t1.start()
	t2.start()



if __name__ == '__main__':	
	app.run(host="0.0.0.0")
	


