FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorios de datos
RUN mkdir -p data/raw data/processed

# Correr ETL estadístico en build para tener datos desde el inicio
RUN python -c "from scripts.etl_estadistico import run_etl_estadistico; run_etl_estadistico()" || echo "ETL warning - continuando"

# Railway inyecta PORT
ENV PORT=8001
EXPOSE $PORT

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
