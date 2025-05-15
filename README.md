# 🛡️ Cybersecurity Control Mapping Tool

This application automatically maps and compares two cybersecurity frameworks (e.g. ISO 27002, TISAX, NIST...) using AI. It assesses coverage between controls and generates gap justifications using a local LLM model (Mistral via Ollama).

---

## 🚀 Features

- Upload two Excel files (source & target frameworks)
- AI-powered control matching using sentence-transformers (MiniLM)
- Filterable coverage donut chart
- Heatmap by control category
- LLM-generated justifications with gap analysis (Mistral via Ollama)
- PDF report export (in memory, no temporary files)
- Fully automated launch via Docker + Ollama

---

## ⚙️ Requirements

- Docker Desktop (Windows, macOS, or Linux)
- Git (optional, for cloning the repository)
- Internet connection (only for first-time model download)

---

## 🧪 First-time Setup

1. Clone the repository:

   git clone https://github.com/yourusername/cyber-mapping-app.git  
   cd cyber-mapping-app

2. Start Ollama and pull the LLM model:

   docker compose up -d ollama  
   docker exec -it ollama ollama pull mistral

3. Launch the app:

   - On **Windows**: double-click `launch.bat`
   - On **Linux/macOS**: run `./launch.sh` in a terminal

---

## 🌐 Access the App

Once running, the app will be available at:

   http://localhost:8501

From the interface, you can:

- Upload your source and target Excel files
- Filter by control category or keyword
- Generate justifications (on demand or in batch)
- Visualize match coverage and heatmap
- Export a PDF report summarizing results

---

## 📁 Project Structure

cyber-mapping-app/  
├── app.py                → Main Streamlit interface  
├── mapping.py            → Control matching & category summary  
├── export_pdf.py         → PDF report generation  
├── llm_utils.py          → LLM API calls to Ollama  
├── requirements.txt      → Python dependencies  
├── Dockerfile            → Streamlit app image  
├── docker-compose.yml    → Compose config (Streamlit + Ollama)  
├── launch.bat            → Windows startup script  
├── launch.sh             → Linux/macOS startup script  
├── LICENSE               → MIT license  
└── README.md             → This file

---

## 📦 LLM Model

This app uses the following local model via Ollama:

   mistral

It will be automatically downloaded the first time using:

   docker exec -it ollama ollama pull mistral

---

## 🛑 Stop the App

To stop all services:

   docker-compose down

---

## 📃 License

This project is licensed under the MIT License. See the LICENSE file for more details.