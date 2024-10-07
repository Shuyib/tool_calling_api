# Use an official Python runtime as the base image
FROM python:3.12-slim

# Install Ollama
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSfL https://ollama.ai/install.sh | sh && \
    ollama run llama3.2:3b

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 7860
EXPOSE 7860

# Define the command to run the application
CMD ["python", "app.py"]