# FROM python:3.11-slim

# WORKDIR /app

# COPY requirements.txt .

# RUN pip3 install --no-cache-dir -r requirements.txt
# RUN find . -name '__pycache__' -exec rm -rf {} + 
# RUN find . -name '*.pyc' -delete

# COPY . .

# COPY wait-for-db.sh /usr/local/bin/
# RUN chmod +x /usr/local/bin/wait-for-db.sh

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "wait-for-db.sh"]

# Use a common slim base image for FastAPI applications
FROM python:3.11-slim

# Install PostgreSQL client tools (pg_isready) and build tools
# 'build-essential' is often needed to compile Python packages like psycopg2
RUN apt-get update && \
    apt-get install -y postgresql-client build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
# Assuming you have a requirements.txt file
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Standard command (overwritten by docker-compose, but good practice)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
