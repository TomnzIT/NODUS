#!/bin/bash

set -e

echo "🚀 Launching NODUS – Cybersecurity Mapping Tool"

# Vérifier que Docker est actif
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running or not installed."
  exit 1
fi

echo ""
echo "🔧 Building the NODUS Docker image..."
docker build -t nodus:latest .

echo ""
echo "📦 Starting containers..."
docker compose up -d

echo ""
echo "✅ App is running at: http://localhost:8501"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"