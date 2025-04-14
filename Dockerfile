# Sử dụng image Python chính thức
FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết (như ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg gcc && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy tất cả các file từ thư mục hiện tại vào trong container
COPY . .

# Cài đặt các thư viện Python từ file requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Chạy ứng dụng của bạn (ví dụ: `python main.py`)
CMD ["python", "main.py"]
