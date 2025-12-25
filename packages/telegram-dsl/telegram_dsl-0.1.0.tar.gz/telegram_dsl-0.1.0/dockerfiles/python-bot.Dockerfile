# Usa Python 3.13 slim per un container leggero
FROM python:3.13-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto nel container
COPY . .

# Installa le dipendenze se è presente un file requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
