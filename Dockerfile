# Render.com için FFmpeg içeren özel kurulum dosyası

# 1. Python 3.9 versiyonunu temel al
FROM python:3.9-slim

# 2. Sistem güncellemelerini yap ve FFmpeg'i kur
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# 3. Çalışma klasörünü ayarla
WORKDIR /app

# 4. Kütüphane listesini kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Tüm kodları kopyala
COPY . .

# 6. Uygulamayı başlat
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
