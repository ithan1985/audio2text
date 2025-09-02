## audio2text

Transcripción offline con **faster-whisper** (CPU) + **ffmpeg** dentro de Docker.

## Requisitos
- Docker y Docker Compose
- (Opcional) Git LFS si vas a versionar audios

## Usar
```bash
docker compose build
docker compose run --rm fwcpu
 
## modelos -m tiny|base|small|medium|large-v3

docker compose run --rm fwcpu \
  "audios/01-09-2025 14.12_fw16k.wav" \
  -o outputs \
  -m small \
  --compute-type int8 \
  --beam-size 5 \
  --vad \
  --progress 10

  