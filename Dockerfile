FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn
COPY . .
EXPOSE 5000
CMD ["sh", "-c", "python -m flask --app app init-db && gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 45 app:app"]
