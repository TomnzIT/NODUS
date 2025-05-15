#!/bin/bash

echo "🔧 Building the cybermap image..."
docker build -t cybermap:latest .

echo "🚀 Starting Docker containers..."
docker compose up -d

echo "✅ App running at: http://localhost:8501"