# Use a slim Python image for high performance
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for uploads
RUN mkdir -p static/uploads

# Expose the port FastAPI will run on
EXPOSE 8080

# Command to run the app (GCP expects port 8080)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]