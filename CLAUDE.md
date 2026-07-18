# CLAUDE.md

Este archivo ofrece guía a Claude Code (claude.ai/code) al trabajar con código en este repositorio.

## Qué es esto

`audio2text` es una herramienta local y offline de transcripción y traducción de audio/video a texto. Corre completamente en Docker sobre CPU — sin llamadas a APIs externas, sin costo de nube. Desarrollada como PoC para la asignatura "Gestión del Conocimiento y Transferencia Tecnológica" en la Universidad Militar Nueva Granada.

Toda la aplicación es un único script: [transcribe.py](transcribe.py). No hay estructura de paquete, no hay suite de pruebas, y no hay paso de build más allá de la imagen Docker.

## Comandos

Todo corre a través de `docker compose run`, que construye la imagen en el primer uso (o tras cambios en `requirements.txt`/`Dockerfile`):

```bash
docker compose run --rm audio2text "audios/audio1.mp3" -l es --translate-to en -m small --vad
```

Reconstruir la imagen explícitamente tras cambios de dependencias:

```bash
docker compose build
```

Flags clave del CLI de `transcribe.py` (ver el bloque `argparse` para la lista completa):

- `-l/--language` — código de idioma origen (string vacío `""` activa autodetección)
- `-m/--model` — `tiny|base|small|medium|large-v3` (default `small`)
- `--translate-to` — código de idioma destino para la traducción con MarianMT
- `--vad` — activa segmentación por detección de actividad de voz (recomendado para audio con ruido)
- `--start` / `--duration` — procesa un rango de tiempo recortado (útil para iterar rápido)
- `--compute-type` — precisión de inferencia en CPU (default `int8`)

No hay suite de pruebas, linter ni formateador configurados en este repo — no asumas que existen `pytest`/`ruff`/etc.

## Arquitectura

Pipeline de un solo paso dentro de `main()` en [transcribe.py](transcribe.py):

1. **`preconvert_to_wav`** — invoca `ffmpeg` (debe estar en el `PATH`; instalado en la imagen Docker) para normalizar cualquier entrada (mp3/m4a/mp4/wav/...) a WAV mono 16kHz PCM en un directorio temporal. Maneja el recorte `--start`/`--duration` vía flags de seek/trim de ffmpeg.
2. **Transcripción** — `faster_whisper.WhisperModel` (Whisper basado en CTranslate2) corre en CPU. Los pesos del modelo se descargan de Hugging Face (`Systran/faster-whisper-*`) en el primer uso y se cachean en `./cache/huggingface` (montado en el contenedor según [docker-compose.yml](docker-compose.yml)).
3. **Escritores de salida** — `write_txt`/`write_srt`/`write_json` toman la misma lista en memoria `segments` (`[{id, start, end, text}, ...]`) y la formatean distinto. Cualquier cambio en la forma de un segmento debe seguir siendo compatible con los tres.
4. **Traducción (opcional)** — `translate_segments` carga un modelo MarianMT `Helsinki-NLP/opus-mt-{src}-{dest}` vía `transformers` y traduce el texto de los segmentos por lotes (batch size 16). Es una *segunda* carga de modelo independiente, separada de Whisper, y solo se activa si se pasa `--translate-to` y `src_lang != dest_lang`. Si el par de idiomas solicitado no existe en Hugging Face, falla en esa ejecución (no es fatal para la transcripción, que ya quedó escrita en disco para ese momento).

Estructura de salida: `outputs/<stem_input>/<stem_input>_<idioma>.{txt,srt,json}`, más `<stem_input>_<idiomaOrigen>-<idiomaDestino>.{txt,srt,json}` cuando corre la traducción. Nota: el paso de transcripción siempre escribe sus propios archivos de salida *antes* de intentar traducir, así que un fallo de traducción nunca hace perder la transcripción.

## Estructura de Docker/volúmenes

[docker-compose.yml](docker-compose.yml) monta:

- `./audios` → `/app/audios` (entradas)
- `./outputs` → `/app/outputs` (salidas; `transcribe.py` usa `/app/outputs` como `outdir` por defecto cuando no se pasa `-o`, así que esto solo tiene sentido dentro del contenedor)
- `./cache/huggingface` y `./cache/ctranslate2` → cachés de modelos HF/CTranslate2, para que los modelos persistan entre ejecuciones del contenedor y no se vuelvan a descargar

El entrypoint está fijo a `python3 transcribe.py`; todos los argumentos de `docker compose run --rm audio2text ...` después del nombre del servicio pasan directo al argparse de `transcribe.py`.

## Notas de plataforma

- En Windows se requiere WSL2 + Ubuntu (Docker no corre nativo); en Mac se requiere Docker Desktop vía Homebrew. Ver [README.md](README.md) para los scripts de onboarding completos (`install-windows.sh`, `install-mac.sh`), que instalan Docker, ffmpeg, y crean un wrapper global `audio2text` en el shell alrededor de `docker compose run`.
- `docker-compose.yml` fija `platform: linux/amd64`, así que en Apple Silicon esto corre bajo emulación.
