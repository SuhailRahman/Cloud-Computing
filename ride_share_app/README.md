## 🧩 Microservices Overview

### 🔹 User Microservice

Manages all user-related operations like user creation and listing.

**Directory**: `user/`  
**Contents**:
- Source code
- `Dockerfile`, `docker-compose.yml`
- `requirements.txt`
- `count.json` – Tracks the number of HTTP requests
- `run.sh` – Shell script to start the service

**To Run**:
```bash
cd user/
./run.sh
````
Pre-requisite:
Before using any APIs, reset the HTTP request count: DELETE /api/v1/_count


## 🔹 Rides Microservice

Handles ride creation, joining, and retrieval operations.

- **Directory**: `rides/`
- **Includes**:
  - Source code
  - `Dockerfile`, `docker-compose.yml`
  - `requirements.txt`
  - `count.json` – Tracks the number of HTTP requests
  - `run.sh` – Shell script to start the service

**To Run**:
```bash
cd rides/
./run.sh
```
Pre-requisite:
Before using any APIs, reset the HTTP request count: DELETE /api/v1/_count

The **Orchestrator** coordinates the user and ride microservices, manages master-slave worker roles, scales worker nodes, and handles leader election using Zookeeper.

- **Directory**: `orchestrator/`
- **Contents**:
  - `database.py` – Core orchestration logic
  - `Dockerfile`, `docker-compose.yml`
  - `requirements.txt`
  - `run.sh` – Shell script to start the service
  - `slave/` folder:
    - `main_worker.py` – Logic for master/slave roles
    - `count1.json` – Maintains the count of active slave instances

**To Run**:
```bash
cd orchestrator/
./run.sh
```
