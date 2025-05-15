@echo off
echo 🔧 Building the NODUS image...
docker build -t nodus:latest .

echo 🚀 Starting containers...
docker-compose up -d

echo ✅ App running at: http://localhost:8501
pause