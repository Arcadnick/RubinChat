FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# When built from repo root: context is ., dockerfile is backend/Dockerfile
COPY backend/requirements.txt .

# pygost is not on PyPI; clone and install (setup.py data_files expect doc-built files)
RUN git clone --depth 1 https://github.com/mosquito/pygost.git /tmp/pygost \
    && cd /tmp/pygost && touch FAQ INSTALL NEWS \
    && pip install --no-cache-dir . \
    && cd / && rm -rf /tmp/pygost

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
