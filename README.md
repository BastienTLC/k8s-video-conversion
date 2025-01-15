# k8s-video-conversion

A video processing application using Kafka for communication between components. The application enables video file uploads through an API, processes them using workers, and stores the results in shared storage.

## Table of Contents
- [Docker Compose Setup](#docker-compose-setup)
- [Kubernetes Setup](#kubernetes-setup)
- [Using the Application](#using-the-application)
- [Load Testing](#load-testing)
- [Monitoring](#monitoring)

## Docker Compose Setup

### Prerequisites
- Docker
- Docker Compose

### Installation and Startup

1. **Launch services**
docker-compose up --build

2. **Check services status**
```
docker-compose logs -f
```
### Cleanup

To stop and remove all services:
```
docker-compose down
```
To remove volumes as well:
```
docker-compose down --volumes
```
## Kubernetes Setup

### Installing Kafka Cluster with Strimzi

1. **Create Kafka namespace**
```
kubectl create namespace kafka
```
3. **Install Strimzi**
```
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
```
5. **Verify operator deployment**
```
kubectl get pod -n kafka --watch
kubectl logs deployment/strimzi-cluster-operator -n kafka -f
```

7. **Deploy Kafka cluster**
```
kubectl apply -f kubernetes/kafka/kafka.yaml -n kafka
```
### Installing MinIO

1. **Deploy MinIO operator**
Follow the official documentation for Helm installation:
https://min.io/docs/minio/kubernetes/upstream/operations/install-deploy-manage/deploy-operator-helm.html

2. **Create MinIO tenant**
Follow the documentation for tenant configuration:
https://min.io/docs/minio/kubernetes/upstream/operations/install-deploy-manage/deploy-minio-tenant.html

### Deploying the Application

Deploy all application components:
```
kubectl apply -f kubernetes/app/
```
### Monitoring

1. **Install Prometheus**
```
helm install -f kubernetes/prometheus/prometheus-values.yaml prometheus prometheus-community/prometheus
```
3. **Configure Kafka monitoring**
```
kubectl apply -f kubernetes/prometheus/strimzi-pod-monitor.yaml
```
### Load Testing

Deploy Locust for performance testing:
```
kubectl apply -f kubernetes/locust/locust-deployment.yaml
```
## Using the Application

### Accessing Interfaces

- **API**: http://localhost:5000
- **Frontend**: http://localhost:3000

### Accessing Dashboards

- **Prometheus**: http://localhost:9090
- **Locust**: http://localhost:8089

## Kubernetes Environment Cleanup

To remove all resources:
```
kubectl delete -f kubernetes/app/
kubectl delete -n kafka -f kubernetes/kafka/kafka.yaml
kubectl delete -f 'https://strimzi.io/install/latest?namespace=kafka'
kubectl delete namespace kafka
```
