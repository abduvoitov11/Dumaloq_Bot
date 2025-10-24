# Python 3.10 asosida
FROM python:3.10-slim

# ffmpeg o'rnatish (video qayta ishlash uchun)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Ishtirokchi fayllarni nusxalash
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot faylini nusxalash
COPY . .

# Portni ochish
EXPOSE 8080

# Botni ishga tushirish
CMD ["python", "main.py"]