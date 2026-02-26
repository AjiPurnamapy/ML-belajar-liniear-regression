# ---- Base Image ----
FROM python:3.11-slim

# Metadata
LABEL maintainer="AjiPurnama"
LABEL description="API Prediksi Gaji V2 — FastAPI + scikit-learn"

# Set working directory
WORKDIR /app

# Hindari buffer pada stdout/stderr (log langsung keluar)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies dulu (layer caching — jarang berubah)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code + model
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Jalankan server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
