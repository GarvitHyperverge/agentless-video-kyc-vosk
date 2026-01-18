FROM python:3.11-slim

# Install system dependencies required by Vosk
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and model
COPY vosk_ws.py .
COPY vosk-model-en-in-0.5/ ./vosk-model-en-in-0.5/

# Expose the WebSocket server port
EXPOSE 2700

# Run the server
CMD ["python3", "vosk_ws.py"]
