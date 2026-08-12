# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for PostgreSQL and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project files
COPY . /app/

# Expose port 7319
EXPOSE 7319

# Default command: collectstatic, migrate, and start Gunicorn on port 7319
CMD python manage.py collectstatic --noinput && \
    python manage.py migrate --noinput && \
    gunicorn --bind 0.0.0.0:7319 --workers 3 --timeout 120 lumora.wsgi:application
