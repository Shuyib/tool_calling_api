# Use an official Python runtime as the base image
FROM python:3.12-slim

# Meta-data
LABEL maintainer="Shuyib" \
      description="Using communication APIs with ollama, LLMs and codecarbon to track CO2 emissions."

# Set the working directory to /app
WORKDIR /app

# ensures that the python output is sent to the terminal without buffering
ENV PYTHONUNBUFFERED=TRUE

# Copy the current directory contents into the container at /app
COPY . /app

# Install Ollama and other dependencies in a single RUN command
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSfL https://ollama.ai/install.sh | sh && \
    ollama run llama3.2:3b && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 7860
EXPOSE 7860

# Define the command to run the application
CMD ["python", "app.py"]
