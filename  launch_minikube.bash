#!/bin/bash

set -e

APP_NAME="bouncing-ball"
IMAGE_NAME="bouncing-ball-server"
NAMESPACE="default"
YAML_DIR="./k8s"

echo "Starting minikube..."
minikube start --driver=docker

echo "Pointing Docker to minikube's daemon..."
eval $(minikube docker-env)

echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Applying Kubernetes manifests..."
kubectl apply -f "$YAML_DIR/deployment.yaml"
kubectl apply -f "$YAML_DIR/service.yaml"

echo "Waiting for deployment to become ready..."
kubectl rollout status deployment/$APP_NAME

echo "Fetching service URL..."
minikube service $APP_NAME --url
