# ─────────────────────────────────────────────────────────────
#  Techno ML App · Dockerfile
#  Base image : python:3.13-slim  (as required by the module)
#  Exposed port: 2000  (techno-sg-apps opens port 2000)
# ─────────────────────────────────────────────────────────────
FROM python:3.13-slim

# Metadata
LABEL maintainer="LKS Cloud Computing Jawa Tengah 2025"
LABEL description="ML-powered image rekognition app"

# Set working directory
WORKDIR /app

# Install OS dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy & install Python dependencies first (layer cache optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .

# Create non-root user for security best practice
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port that Security Group techno-sg-apps allows
EXPOSE 2000

# Health-check (used by EKS liveness probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:2000/health || exit 1

# Start the application
CMD ["python", "app.py"]
