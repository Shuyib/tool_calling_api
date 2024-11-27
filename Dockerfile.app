# Dockerfile for the app container
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .
COPY app.py .
COPY utils/ ./utils/

# update, upgrade and install required packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv .venv \
    && . .venv/bin/activate \
    && pip --no-cache-dir install --upgrade pip \
    && pip --no-cache-dir install -r requirements.txt 

# Set the environment variables
ENV OLLAMA_HOST=http://ollama:11434

# Export the port
EXPOSE 7860

# command to run on container start
CMD [".venv/bin/python", "app.py"]
