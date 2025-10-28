# Usar una imagen base de Python específica para mayor reproducibilidad
FROM python:3.11-slim-bookworm

# Etiqueta para identificar al mantenedor
LABEL maintainer="Ithan"

# Instalar ffmpeg y sus dependencias desde los repositorios de Debian
# --no-install-recommends evita instalar paquetes innecesarios
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    # Limpiar la caché de apt para mantener la imagen ligera
    rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación al directorio de trabajo
COPY . .