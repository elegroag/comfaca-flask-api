FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ENV PATH="/app/.local/bin:${PATH}"

# Dependencias del sistema requeridas por WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app

USER app

RUN pip install --no-cache-dir \
    weasyprint \
    python-dotenv \
    jinja2 \
    "fonttools>=4.60.1" \
    flask \
    gunicorn \
    gevent-websocket


#CMD ["python", "app.py"]
CMD ["python", "-m", "gunicorn", "--config", "gunicorn_config.py", "wsgi:application"]

EXPOSE 80/tcp
