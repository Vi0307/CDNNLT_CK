# ---- Base image ----
FROM python:3.11-slim

# ---- Metadata ----
LABEL maintainer="process-service"
LABEL description="Microservice xử lý Blog thành Podcast"

# ---- Thư mục làm việc bên trong container ----
WORKDIR /app

# ---- Copy và cài đặt dependencies trước (tận dụng Docker cache) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy toàn bộ source code ----
COPY . .

# ---- Expose port 8002 ----
EXPOSE 8002

# ---- Lệnh khởi chạy ứng dụng ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
