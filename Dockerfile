# Use the Python 3.12 slim image as base
FROM python:3.12-slim

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies for Caddy
RUN apt update && \
    apt install -y debian-keyring debian-archive-keyring apt-transport-https curl && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt update && \
    apt install -y caddy

# Set up the Caddyfile configuration
RUN echo "ttsbackend.inraysmiv.xyz {" > /etc/caddy/Caddyfile && \
    echo "    reverse_proxy localhost:8000" >> /etc/caddy/Caddyfile && \
    echo "}" >> /etc/caddy/Caddyfile

# Copy application code
COPY . /app/

# Expose the application port
EXPOSE 8000

# Start the Django application
CMD ["python", "manage.py", "runserver"]
