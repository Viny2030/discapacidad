FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorios de datos que el ETL necesita
RUN mkdir -p data/raw data/processed

# Railway inyecta PORT como variable de entorno
ENV PORT=8001

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
