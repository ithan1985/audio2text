# Dockerfile (CPU only)
FROM python:3.11-slim

# ffmpeg para leer m4a/mp3/wav/mp4
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Librerías necesarias
RUN pip install --no-cache-dir faster-whisper==1.0.3 rich==13.7.1

WORKDIR /app
COPY transcribe.py /app/transcribe.py

ENTRYPOINT ["python", "/app/transcribe.py"]
