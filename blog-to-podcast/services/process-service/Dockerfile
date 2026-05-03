# ---- Base image ----
FROM python:3.11-slim

LABEL maintainer="process-service"
LABEL description="Microservice xử lý Blog thành Podcast"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Giữ package app/ dưới /app/app để import app.main, app.config hoạt động
COPY app ./app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
