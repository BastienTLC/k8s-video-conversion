# k8s-video-conversion


# Video Processing Application with Kafka

This application processes video files uploaded via an API, converts them using a worker, and stores the results in a shared storage. The communication is managed through Kafka.

---

## **How to Run with Docker**

1. **Start the services with Docker Compose**  
   Use the following command to start the services (API, Kafka, Worker, Frontend):
   ```bash
   docker-compose up --build
   ```

2. **Verify the services**  
   Ensure all services are running by checking their logs:
   ```bash
   docker-compose logs -f
   ```

---

## **How to Run with Kubernetes**

1. **Start the services with Kubectl**  
    Use the following command to start the services (API, Kafka, Worker, Frontend):
    ```bash
    kubectl apply -f manifest.yaml
    ```

2. **Verify the services**  
    Ensure everything is running by checking services, pods, etc.:
    ```bash
    kubectl get svc
    kubectl get pod
    ```

3. **Forward the frontend and API**  
    Expose the frontend and the API outside the cluster:
    ```bash
    kubectl port-forward svc/frontend 8080:80    
    kubectl port-forward svc/flask-api-service 5000:5000
    ```

---

## **Creating Kafka Topics**

To enable the communication between the API and Worker, create the required Kafka topics.

1. **Access the Kafka container**  
   Execute the following command to open a shell inside the Kafka container:
   ```bash
   docker exec -it kafka bash
   ```

2. **Create the `task_queue` topic**  
   Use the `kafka-topics.sh` script to create the topic:
   ```bash
   kafka-topics.sh --create --topic task_queue --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1
   ```

3. **Create the `result_queue` topic**  
   Similarly, create the second topic:
   ```bash
   kafka-topics.sh --create --topic result_queue --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1
   ```

4. **Verify the topics**  
   List all topics to ensure they were created successfully:
   ```bash
   kafka-topics.sh --list --bootstrap-server kafka:9092
   ```

---

## **Access the Application**

- **API**:  
  The API runs on `http://localhost:5000`. Use a tool like Postman or `curl` to interact with it.

- **Frontend**:  
  Access the frontend interface at `http://localhost:3000`.

---

## **Cleanup**

To stop and remove all services:
```bash
docker-compose down
```

To remove all volumes and clean up storage:
```bash
docker-compose down --volumes
```
```

To stop and remove all ressources form cluster:
```bash
kubectl delete -f manifest.yaml
```