User micro-service:
The "user" folder contains the source code of the user micro-service, Dockerfile, docker-compose file, requirements.txt, count.json (which contains the number of HTTP requests), and a bash file. The command to run the micro-service is ./run.sh. Pre-requisite: Before running any other api ,reset the http count value to zero by using "api/v1/_count" using "Delete" Method  .

Rides micro-service:
The "rides" folder contains the source code of the rides micro-service, Dockerfile, docker-compose file, requirements.txt, count.json (which contains the number of HTTP requests), and a bash file. The command to run the micro-service is ./run.sh. Pre-requisite: Before running any other api ,reset the http count value to zero by using "api/v1/_count" using "Delete" Method .

Orchestrator:
The "orch_trial" folder contains database.py(the source code for orchestrator) , Dockerfile, docker-compose file, requirements.txt, a bash file, and slave folder. The slave folder contains main_worker.py (source code for the worker program i.e. Master and Slave program ) and count1.json (to keep track of the number of slaves).  Before you start running the program, reset the counters in the "slave/count1.json" to 1. The command to run the micro-service is ./run.sh


