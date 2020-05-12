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
import sys
import uuid
import ast
import threading
import math
import docker
import time
from time import time as timer
import subprocess
from kazoo.client import KazooClient
from kazoo.client import KazooState
import logging

logging.basicConfig()


zk= KazooClient(hosts='zoo:2181')
zk.start()
zk.ensure_path("/orchestrator")

#client=docker.from_env()

slave_num=1

flag = 0

client = docker.DockerClient(base_url='unix://var/run/docker.sock')

global count_all 
count_all=0

global count
count=0
timeout = 120


app = Flask(__name__)



#------------------------------------------------------------------------

class Read_response(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='read_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return (self.response)

#hi=client.containers.run('orch_slave', name='slave_7', command='sh -c "sleep 15 && python slave/main_worker.py slave"', volumes={'/home/ubuntu/orch/slave/main_worker.py': {'bind': '/src/main_worker.py', 'mode': 'ro'}},detach=True)
container1=client.containers.run('orchtrial_master', name="master", command='sh -c "python3 -u slave/main_worker.py master"',environment=["TEAM_NAME=cc_1271_1403_1420_1814"],network="orchtrial_default", volumes={'/home/ubuntu/orch_trial/': {'bind': '/code', 'mode': 'rw'},'/usr/bin/docker':{'bind':'/usr/bin/docker'},'/var/run/docker.sock':{'bind':'/var/run/docker.sock'}},detach=True)
time.sleep(1)
container2=client.containers.run('orchtrial_slave', name="slave" ,command='sh -c "python3 -u slave/main_worker.py slave"', environment=["TEAM_NAME=cc_1271_1403_1420_1814"],network="orchtrial_default", volumes={'/home/ubuntu/orch_trial/': {'bind': '/code', 'mode': 'rw'},'/usr/bin/docker':{'bind':'/usr/bin/docker'},'/var/run/docker.sock':{'bind':'/var/run/docker.sock'}},detach=True)
print("master----",container1.id)
print("slave-----",container2.id)
#os.system("docker inspect -f '{{.State.Pid}}'"+container1.id+" > slave/pid.txt ")
#os.system("docker inspect -f '{{.State.Pid}}'"+container2.id+" > slave/pid.txt ")
st=""
proc = subprocess.Popen(["docker inspect -f '{{.State.Pid}}' "+container1.id], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
print(out.decode("utf-8"))
time.sleep(1)
#Leader election
children = zk.get_children("/orchestrator")
print("There are %s children with names %s" % (len(children), children))

min_pid=int(children[0])
for i in children:
	if(int(i)<min_pid):
		min_pid=int(i)	

data, stat = zk.get("/orchestrator/"+str(min_pid).strip())
print("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))

zk.set("/orchestrator/"+str(min_pid).strip(),b"1")
print("Master is (pid):",min_pid)

data, stat = zk.get("/orchestrator/"+str(min_pid).strip())
print("Version: %s, data of master: %s" % (stat.version, data.decode("utf-8")))



def get_pid():
	os.system('pgrep containerd-shim > tmp.txt')
	with open('tmp.txt','r') as l:
		sline=l.readlines()
	sline=[x.strip() for x in sline]
	#print(sline)
	container_pid.append(sline[-1])
	print("pid",container_pid)


def gfg():
	global count
	ct=count/20
	num=math.ceil(ct)
	if(num==0):
		num=1
	count=0
	n=0
	global flag
	global slave_num

	with open('slave/count1.json') as f:
		data=json.load(f)
	slave = data["slave"]
	database_count = data["count"]
	print("num",num)
	print("slave",slave)
	result= num-slave
	print("result before if ",result)
	if(result>0):
		#data["slave"]=num

		#with open('slave/count1.json','w') as json_file:
			#json.dump(data,json_file)
		for n in range(result):
			
			with open('slave/count1.json') as f:
				data=json.load(f)
			count=int(data["count"])
			data["count"]=count+1
			with open('slave/count1.json','w') as json_file:
				json.dump(data,json_file)

			
			flag = 1
			st=""
			
			nm='slave'+str(slave_num)
			container_id = client.containers.run('orchtrial_slave', name=nm, command='sh -c "python3 -u slave/main_worker.py slave"',environment=["TEAM_NAME=cc_1271_1403_1420_1814"],network="orchtrial_default", volumes={'/home/ubuntu/orch_trial/': {'bind': '/code', 'mode': 'rw'},'/usr/bin/docker':{'bind':'/usr/bin/docker'},'/var/run/docker.sock':{'bind':'/var/run/docker.sock'}}, detach=True)
			
			data["slave"]=slave+1+n
			with open('slave/count1.json','w') as json_file:
				json.dump(data,json_file)
			time.sleep(3)
			flag = 0
			print( nm  ,"is created")
			
			slave_num = slave_num+1
			


	if(result<0):
	#if(0):
		data["slave"]=num
		print("result",result)
		with open('slave/count1.json','w') as json_file:
			json.dump(data,json_file)	

		for i in range (abs(result)):

			

			temp=client.containers.list()
			
			print("container list",temp)
			
			container_name=client.containers.get(str(temp[0].id))
			print("slave is going to get deleted ",container_name)
			container_name.kill()
			



def mytime():
    deadline = timer() + timeout # reset
    while True:
        if (deadline < timer()): # timeout
            deadline = timer() + timeout # reset
            gfg()

#------------------------------------------------------------------------
@app.route("/api/v1/db/read",methods=["POST"])

def read():
    
	global count_all
	global count
	count_all+=1
	count+=1
	#timer = threading.Timer(12.0, gfg)
	if(count_all==1):
		t = threading.Thread(target =mytime)
		t.start()
	print(count_all)
	print(count)

	data=request.get_json()
	table=data['table']

	#Read users
	if(table=="user"):
		fibonacci_rpc = Read_response()
		message="user;"
		response = fibonacci_rpc.call(message)
		response=response.decode("utf-8")
		new = ast.literal_eval(response)
		if(len(new)!=0):
			return jsonify(new)
		return "0"

	#Read rides
	if(table=="ride"):

		id = data['id']

		if(id=="1"):
			rideid=data['rideid']
			fibonacci_rpc = Read_response()
			message="ride;1;"+rideid+";"
			print(message)
			response = fibonacci_rpc.call(message)
			response=response.decode("utf-8")
			new = ast.literal_eval(response)
			print(new)
			if(new=="0" or new==0):
				return "0"
			if(len(new)!=0):
					return jsonify(new)
			

		if(id=="2"):
			source=data['source']
			destination=data['destination']
			fibonacci_rpc = Read_response()
			message="ride;2"+";"+source+";"+destination+";"
			response = fibonacci_rpc.call(message)
			response=response.decode("utf-8")
			output = ast.literal_eval(response)
			if(len(output)==0):
				output=[]
			ride=[]
			flag=False
			if(int(source)<1 or int(source)>198) and (int(destination)<1 or int(destination)>198):
				return "1"
			for details in output:
				d={}
				d.update(details)
				d.pop("source")
				d.pop("destination")
				#d.pop("users")
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

		if(id=="3"):
			fibonacci_rpc = Read_response()
			message="ride;3;"
			response = fibonacci_rpc.call(message)
			response=response.decode("utf-8")
			x = ast.literal_eval(response)
			l=[]
			l.append(x)
			return jsonify(l)

#------------------------------------------------------------------------------------------

#Writing to db
@app.route("/api/v1/db/write",methods=["POST"])
def write():


	# with open('count.json') as f:
	# 	data=json.load(f)
	# data["write_count"]+=1
	# with open('count.json','w') as json_file:
	# 	json.dump(data,json_file)

	
	global flag
	while(flag):
		continue

	data=request.get_json()
	table=data['table']

	if(table=="clear"):
		connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rmq'))
		channel = connection.channel()
		channel.queue_declare(queue='write_queue', durable=True)
		message ="clear;"
		channel.basic_publish(exchange='',routing_key='write_queue',
			    body=message,
			    properties=pika.BasicProperties(
			        delivery_mode=2,  # make message persistent
			    ))
		print(" [x] Sent %r" % message)
		connection.close()
		return "1"

	#Add user
	if(table=="user"):
		method=data['type']
		if(method=="PUT"):
			username=data['username']
			password=data['password']
			connection = pika.BlockingConnection(
		    pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.queue_declare(queue='write_queue', durable=True)
			message ="user;PUT;"+username+";"+password+";"
			channel.basic_publish(exchange='',routing_key='write_queue',
			    body=message,
			    properties=pika.BasicProperties(
			        delivery_mode=2,  # make message persistent
			    ))
			print(" [x] Sent %r" % message)
			connection.close()
			return "1"

		#Remove user
		elif(method=='DELETE'):
			username=data['username']
			connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.queue_declare(queue='write_queue', durable=True)
			message ="user;DELETE;"+username+";"
			channel.basic_publish(exchange='',routing_key='write_queue',body=message,properties=pika.BasicProperties(delivery_mode=2,))
			print(" [x] Sent %r" % message)
			connection.close()
			return "1"


	#Add rides		
	if(table=="ride"):

		id = data['id']

		#Creating rides
		if(id=="1"):
			created_by=data['created_by']
			timestamp=data['timestamp']
			source=data['source']
			destination=data['destination']
			connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.queue_declare(queue='write_queue', durable=True)
			message ="ride;1;"+created_by+";"+timestamp+";"+source+";"+destination+";"
			channel.basic_publish(exchange='',routing_key='write_queue',body=message,properties=pika.BasicProperties(delivery_mode=2,))
			print(" [x] Sent %r" % message)
			connection.close()
			return "1"
		
		#Join an existing ride
		if(id=="2"):
			rideid=data['rideid']
			username=data['username']
			output=data['output']
			print("users ",output)
			print("username ",username)
			if bool(username in output):
				connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
				channel = connection.channel()
				channel.queue_declare(queue='write_queue', durable=True)
				message ="ride;2;"+rideid+";"+username+";"
				channel.basic_publish(exchange='',routing_key='write_queue',body=message,properties=pika.BasicProperties(delivery_mode=2,))
				print(" [x] Sent %r" % message)
				connection.close()
				return "1"
			return "2"

		#Deleting a ride
		if(id=="3"):
			rideid=data['rideid']
			connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.queue_declare(queue='write_queue', durable=True)
			message ="ride;3;"+rideid+";"
			channel.basic_publish(exchange='',routing_key='write_queue',body=message,properties=pika.BasicProperties(delivery_mode=2,))
			print(" [x] Sent %r" % message)
			connection.close()
			return "1"


#------------------------------------------------------------------------------------------
#Killing a slave

@app.route('/api/v1/worker/list',methods=['GET'])
def get_workers():
	if(request.method!="GET"):
		abort(405)
	children = zk.get_children("/orchestrator")
	print("There are %s children with names %s" % (len(children), children))
	l=[]
	for i in range(len(children)):
		l.append(int(children[i]))
	l.sort()
	print(l)
	return jsonify(l),200

@app.route('/api/v1/crash/slave',methods=['POST'])
def crash_slave():
	if(request.method!="POST"):
		abort(405)
	list_pid = requests.get(request.url_root+"api/v1/worker/list")
	list_pid= list_pid.json()
	top_pid = list_pid[-1]
	data, stat = zk.get("/orchestrator/"+str(top_pid).strip())
	print("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))
	s = data.decode("utf-8")

	if (s=="0"):

		x="docker ps -q | xargs docker inspect --format '{{.State.Pid}}, {{.Id}}' | grep "+str(top_pid).strip()
		proc = subprocess.Popen([x], stdout=subprocess.PIPE, shell=True)
		(out, err) = proc.communicate()
		out=out.decode("utf-8")
		l=out.split(",")
		print("container_id",str(l[1]))
		cid=str(l[1]).strip()
		container_name=client.containers.get(str(cid))
		print("slave is going to get deleted ",container_name)
		container_name.kill()
		container_name.remove()
		zk.delete("/orchestrator/"+ str(top_pid).strip())
		global flag
		flag=1
		time.sleep(1)
		flag=0
		#with open('slave/count1.json') as f:
		#	data=json.load(f)
		#data["slave"]-=1
		#print("result",result)
		#with open('slave/count1.json','w') as json_file:
		#	json.dump(data,json_file)
		l=[]
		l.append(top_pid)
		return jsonify(l),200


@app.route('/api/v1/crash/master',methods=['POST'])
def crash_master():
	if(request.method!="POST"):
		abort(405)
	list_pid = requests.get(request.url_root+"api/v1/worker/list")
	list_pid= list_pid.json()
	top_pid = list_pid[0]
	data, stat = zk.get("/orchestrator/"+str(top_pid).strip())
	print("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))
	s = data.decode("utf-8")

	if (s=="1"):

		x="docker ps -q | xargs docker inspect --format '{{.State.Pid}}, {{.Id}}' | grep "+str(top_pid).strip()
		proc = subprocess.Popen([x], stdout=subprocess.PIPE, shell=True)
		(out, err) = proc.communicate()
		out=out.decode("utf-8")
		l=out.split(",")
		print("container_id",str(l[1]))
		cid=str(l[1]).strip()
		container_name=client.containers.get(str(cid))
		print("slave is going to get deleted ",container_name)
		container_name.kill()
		container_name.remove()
		zk.delete("/orchestrator/"+ str(top_pid).strip())
		l=[]
		l.append(top_pid)
		return jsonify(l),200



@zk.ChildrenWatch('/orchestrator')
def demo_func(child):
	global slave_num
	with open('slave/count1.json') as f:
		data=json.load(f)
	slave = data["slave"]
	db=data["count"]
	print(child)
	slave_list=[]
	for i in child:
		data,stat=zk.get('/orchestrator/'+str(i).strip())
		if(data.decode('utf-8')=='0'):
			slave_list.append(i)
	print(slave_list)
	slaves=len(slave_list)
	with open('slave/count1.json') as f:
		data=json.load(f)
	slave = data["slave"]
	result=slaves-slave
	print("result inside watch",result)
	if(result==0):
		print("All slaves are working properly ")
	if(result<0):
		#with open('slave/count1.json') as f:
		#	data=json.load(f)
		#db=data["count"]
		for i in range(abs(result)):
			with open('slave/count1.json') as f:
				data=json.load(f)
			count=int(data["count"])
			data["count"]=count+1
			with open('slave/count1.json','w') as json_file:
				json.dump(data,json_file)
			nm='slave'+str(slave_num)
			container_slave=client.containers.run('orchtrial_slave', name=nm, command='sh -c "python3 -u slave/main_worker.py slave"',environment=["TEAM_NAME=cc_1271_1403_1420_1814"],network="orchtrial_default", volumes={'/home/ubuntu/orch_trial/': {'bind': '/code', 'mode': 'rw'},'/usr/bin/docker':{'bind':'/usr/bin/docker'},'/var/run/docker.sock':{'bind':'/var/run/docker.sock'}},detach=True)
			slave_num = slave_num+1
			time.sleep(3)



if __name__ == '__main__':
	app.run(host='0.0.0.0',port=80)
