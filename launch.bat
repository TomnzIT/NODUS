@echo off
title 🚀 Launching NODUS - Cyber Mapping Tool

echo Checking Docker installation...
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed or not in PATH.
    pause
    exit /b
)

docker compose version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not available.
    pause
    exit /b
)

echo.
echo 🔧 Building the NODUS image...
docker build -t nodus:latest .

echo.
echo 🚀 Starting containers...
docker compose up -d

echo.
echo ✅ App is running at: http://localhost:8501
pause