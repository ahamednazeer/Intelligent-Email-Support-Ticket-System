# =========================
# Stage 1: Builder
# =========================
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

WORKDIR /app

# Install only essential build dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies (binary wheels preferred)
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt


# =========================
# Stage 2: Runner
# =========================
FROM python:3.11-slim

WORKDIR /app

# Copy only virtual environment
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy app
COPY . .

EXPOSE 8000

# FastAPI production start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]