# ===========================================
# 1. BUILDER STAGE – install deps + compile
# ===========================================
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system build deps
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    gcc \
    graphviz \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python deps into a relocatable folder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy project source
COPY . /app/

# (Optional) create runtime directories exactly like your current Dockerfile
RUN mkdir -p generated_diagrams \
    && mkdir -p frontend/static/css \
    && mkdir -p tests \
    && mkdir -p setup/logs

# Compile to optimized bytecode only
RUN python -m compileall -b .

# Remove source .py files from builder (optional)
RUN find . -name "*.py" -type f -delete


# ===========================================
# 2. RUNTIME STAGE – LIGHTWEIGHT, NO SOURCE
# ===========================================
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    graphviz \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled site-packages
COPY --from=builder /install /usr/local

# Copy compiled Django project (only .pyc + non-Python files)
COPY --from=builder /app /app

# Final sanity check: remove any accidental .py files
RUN find . -name "*.py" -type f -delete

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]