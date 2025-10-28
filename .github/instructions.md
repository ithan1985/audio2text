
# Instrucciones para el proyecto `audio2text`

## Resumen del Proyecto
- **audio2text** es una herramienta de transcripción de audio/video que funciona sin conexión, usando `faster-whisper` (optimizado para CPU) y `ffmpeg`. Todo el entorno está empaquetado con Docker para facilitar su uso.  
- **Flujo principal:** Transcribir archivos de audio/video de la carpeta `audios/` a archivos de texto (`.txt`, `.srt`, `.json`) en la carpeta `outputs/`. Los modelos de IA se guardan en la carpeta `cache/` para evitar descargas repetidas.  

## Arquitectura y Flujo de Datos
- **Punto de entrada:** El script `transcribe.py` es el núcleo de la aplicación y se invoca a través de Docker Compose.  
- **Entrada de audio:** Coloca tus archivos de audio o video en la carpeta `audios/` (soporta `.m4a`, `.mp3`, `.mp4`, `.mov`, etc.).  
- **Salida de transcripción:** Los resultados se guardan en `outputs/`, dentro de una subcarpeta con el mismo nombre del archivo de audio.  
- **Caché de modelos:** Los modelos de Whisper y de traducción se guardan en las carpetas `cache/` para no tener que descargarlos cada vez.  
- **Orquestación con Docker:**
  - `docker-compose.yml` define el servicio `audio2text` y sus parámetros por defecto.  
  - `Dockerfile` construye la imagen del contenedor con todas las dependencias necesarias.  

## Flujos de Trabajo
- **1. Construir el contenedor (solo la primera vez o si cambias dependencias):**
  ```bash
  docker compose build
  ```
- **Ejecutar transcripción:**
  ```bash
  docker compose run --rm fwcpu "audios/audio.*" -o outputs -m medium --compute-type int8 --beam-size 5 --vad --progress 10
  ```
  - `-m` selecciona el tamaño del modelo (`tiny`, `base`, `small`, `medium`, `large-v3`)  
  - Las salidas se generan en `outputs/`  
- **Depuración:**
  - Revisa los logs de Docker para identificar errores  
  - Verifica en `outputs/` los archivos esperados  
- **Gestión de modelos:**
  - Los modelos se descargan y almacenan automáticamente en `cache/huggingface/hub/`  

## Patrones Específicos del Proyecto
- Todo el procesamiento está contenerizado; no se recomienda ejecutar Python localmente.  
- Los archivos de audio deben estar claramente nombrados y ubicados en `audios/`.  
- Los archivos de salida se nombran igual que el archivo de entrada (ejemplo: `audio1.m4a` → `audio1.txt`).  
- Se recomienda usar `--vad` y `--beam-size` para mejorar la precisión de la transcripción.  

## Puntos de Integración
- **Dependencias externas:**
  - [faster-whisper](https://github.com/Systran/faster-whisper) (transcripción)  
  - ffmpeg (preprocesamiento de audio)  
  - Docker Compose (orquestación)  
- **No existen dependencias en la nube; todo funciona localmente y sin conexión.**  

## Archivos y Directorios Clave
- `transcribe.py`: script principal con la lógica de transcripción  
- `docker-compose.yml`, `Dockerfile`: configuración del contenedor  
- `audios/`: archivos de entrada  
- `outputs/`: resultados de la transcripción  
- `cache/huggingface/hub/`: caché de modelos  

## Ejemplo de Comando y de Ejecución Ingles (en) a Español (es)
```bash
docker compose run --rm audio2text "audios/audio1.m4a" -l en --translate-to es -m small --vad
```
## Ejemplo de Comando y de Ejecución Alemán (de) a Francés (fr)
```bash
docker compose run --rm audio2text "audios/audio1.m4a" -l de --translate-to fr -m small --vad
```