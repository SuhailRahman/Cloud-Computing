# Ride-Sharing Application – Cloud-Native Microservices Architecture

This project is a cloud-based ride-sharing application developed using microservices architecture. It is designed for scalability, fault tolerance, and strong consistency, and deployed on AWS EC2 instances using containerization.

The system consists of three primary microservices:

- **User Service**: Handles user registration and management.
- **Rides Service**: Manages ride creation, joining rides, and ride history.
- **Orchestrator Service**: Coordinates service communication, handles leader election, and manages dynamic scaling logic.

All services are built with **Python**, using **Flask** as the web framework and **SQLAlchemy** as the ORM over a **SQLite3** database. The application makes use of **RabbitMQ** for inter-service messaging and **Zookeeper** for orchestrating leader election in the master-slave setup.

Each microservice is containerized using **Docker** and orchestrated using **Docker Compose**. Services can be started using their respective shell scripts (`run.sh`), and request counting is enabled via a dedicated JSON file (`count.json`).

### Architecture & Deployment

- **Deployment Platform**: AWS EC2 Instances
- **Traffic Routing**: AWS Application Load Balancer is used to route HTTP requests to appropriate microservice instances.
- **Scalability**: 
  - The system follows a **master-slave architecture**.
  - Only slave nodes are scaled horizontally and serve **read-only** operations.
- **Consistency Model**: Uses **synchronous replication** between master and slaves to ensure **strong consistency** across the system.
- **Leader Election**: Managed by Zookeeper to maintain a single active master node.

### Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite3
- **ORM**: SQLAlchemy
- **Messaging**: RabbitMQ
- **Coordination**: Zookeeper (for leader election)
- **Concurrency**: Python multithreading
- **Containerization**: Docker, Docker Compose
- **Deployment**: AWS EC2 with Application Load Balancer

### Setup & Usage

To run each microservice:

1. Navigate to the service directory (e.g. `user/`, `rides/`, or `orchestrator/`)
2. Run:
   ```bash
   ./run.sh


