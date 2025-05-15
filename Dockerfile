FROM python:3.10-slim

# Pour éviter les bugs d'encodage
ENV PYTHONUTF8=1

# Installer les dépendances système nécessaires (matplotlib, reportlab, BERT, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Définir le dossier de travail
WORKDIR /app
COPY . /app

# Installer les packages Python
RUN pip install --no-cache-dir --upgrade "pip<24" && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.headless=true", "--server.enableCORS=false"]