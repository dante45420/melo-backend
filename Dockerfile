FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py

# Migraciones + seed + arranque (seed es idempotente: no hace nada si ya hay data)
CMD flask db upgrade && python scripts/seed.py && gunicorn --bind 0.0.0.0:$PORT run:app
