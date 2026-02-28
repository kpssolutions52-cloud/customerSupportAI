# Multi-tenant Customer Support AI — Backend
# Python 3.11 slim; run with uvicorn
FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run uvicorn (override with docker-compose or -e)
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
