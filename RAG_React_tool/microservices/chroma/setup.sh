#!/bin/bash

set -e

echo "🛠️ Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "🐳 Installing Docker..."
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu  # Apply this after logout/login

echo "📦 Installing Minikube..."
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

echo "📦 Installing kubectl..."
curl -LO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

echo "🚀 Starting Minikube with Docker driver..."
minikube start --driver=docker --cpus=2 --memory=6g

echo "📊 Enabling metrics-server addon..."
minikube addons enable metrics-server

echo "✅ Done. You can now run 'kubectl get pods -A' to see system pods."

echo "⚠️ IMPORTANT: Run 'exit' and reconnect via SSH to activate Docker group changes."

