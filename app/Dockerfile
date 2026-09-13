# ---- Build stage (keeps final image small) ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# tzdata is required by stdlib zoneinfo on slim images.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring in the installed packages from the builder.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY app ./app

# Render injects PORT; gunicorn binds to it.
# 4 workers is a good default for a CPU-light API; tune to 2*CPU in production.
CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:10000", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
