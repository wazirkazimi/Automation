# Dockerfile for Railway (and other container platforms)
# Uses python:3.12-slim and installs ffmpeg and build deps so MoviePy + gevent (optional) can build

FROM python:3.12-slim

# Prevents Python from writing .pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (ffmpeg + build tools for optional native packages)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       gcc \
       build-essential \
       libffi-dev \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Create uploads/outputs folders and set permissions
RUN mkdir -p /app/uploads /app/outputs && chown -R root:root /app

# Railway sets PORT env var — default to 5000 if not set
ENV PORT=5000

# Use gthread worker by default to avoid gevent native build issues; if you installed gevent, you can change to gevent worker
CMD ["gunicorn", "--workers", "4", "--worker-class", "gthread", "--threads", "4", "--timeout", "300", "--bind", "0.0.0.0:$PORT", "app:app"]
