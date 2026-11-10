# Production image for the Flask API.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENV_NAME=production \
    UPLOAD_DIR=/data/uploads

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/uploads \
    && chown -R app:app /data /app
USER app

EXPOSE 8000

# Apply migrations, then serve. Render and Railway pass $PORT.
CMD ["sh", "-c", "flask --app run.py db upgrade --directory migrations && exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120 --access-logfile - run:app"]
