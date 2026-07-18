# TODO / Mejoras propuestas

Lista de mejoras identificadas al revisar el repositorio (código, Docker, README, instaladores). No implica ningún cambio realizado — solo propuestas.

## Correctitud / bugs potenciales

- **`--vad` puede dejar `segments` vacío sin avisar por qué.** Si el VAD filtra todo el audio (silencio o ruido puro), el script imprime "No se detectaron segmentos" y termina sin error — pero no distingue entre "audio vacío" y "VAD demasiado agresivo". Sería útil loguear la duración detectada por `info.duration` en ese caso para diagnosticar.
- **Fallo de traducción no siempre queda claro para el usuario.** `translate_segments` imprime a `stderr` y retorna `success=False`, pero el proceso termina con código 0 igualmente (la traducción es "best effort"). Si el objetivo es un pipeline automatizado, esto puede esconder errores silenciosamente.
- **`in_path.stem` puede colisionar.** Si dos archivos de entrada distintos comparten el mismo *stem* (p. ej. `audio.mp3` y `audio.wav`), ambos escriben en `outputs/audio/`, sobrescribiendo resultados previos sin aviso.
- **`args.language.strip()`** no valida que el código de idioma sea válido antes de pasarlo a Whisper; un typo (`-l esp`) fallará tarde, dentro de `model.transcribe`, con un traceback poco amigable para usuarios no técnicos (el público objetivo del README es no técnico).

## Consistencia README ↔ código

- El README dice *"El texto transcrito tiene muchos errores → activa `--vad`"*, pero no menciona que `--vad` es un flag booleano sin argumentos — está bien documentado, es solo una nota menor de claridad.
- El README no documenta `--compute-type`, `--beam-size`, `--progress`, `--cpu-threads` ni `--num-workers`, que sí existen en `transcribe.py`. Usuarios avanzados no tienen forma de descubrirlos sin leer el código.
- El README menciona 11 idiomas soportados "para traducción", pero en la práctica cualquier par soportado por `Helsinki-NLP/opus-mt-*` en Hugging Face funcionaría (o fallará limpiamente si no existe el par). Vale la pena aclarar que la lista es orientativa, no exhaustiva.

## Housekeeping del repo

- **`audio_base/` está sin trackear (`git status` lo muestra como untracked) mientras `audios/*.mp3` aparecen como eliminados.** Parece una reorganización en curso (mover los audios de ejemplo a `audio_base/`). Si esa es la intención, falta decidir si `audio_base/` va en `.gitignore` (como `audios/` implícitamente vía `cache/`/`outputs/`) o si se trackea con Git LFS — el repo ya usa LFS (`.gitattributes`, objetos en `.git/lfs/`), pero `.gitattributes` solo declara `*.sh text eol=lf`, no reglas LFS para `*.mp3`.
- **`.gitignore` tiene entradas duplicadas** (`outputs/`, `cache/`, `__pycache__/`, `*.pyc`, `.env` aparecen dos veces — líneas 2-5 y 19-23). No afecta funcionalidad pero conviene limpiarlo.
- **`__pycache__/` versionado en disco con un `.pyc` de Python 3.14** (`transcribe.cpython-314.pyc`) — está en `.gitignore` así que no se sube, pero indica que se ejecutó `transcribe.py` con un intérprete local (3.14) distinto al de la imagen Docker (3.11-slim-bookworm). Podría ser fuente de confusión para debugging si alguien asume que el entorno local coincide con el de Docker.
- **`cache/` local pesa ~11 GB** (varios modelos Whisper tiny/small/medium + 6 pares de modelos Helsinki-NLP, más `cache/huggingface/xet` con 4.3 GB de chunks). Vale la pena documentar en el README cuánto espacio en disco se necesita antes de empezar, y opcionalmente un comando de limpieza (`docker compose run --rm audio2text ...` no borra caches viejos si el usuario cambia de modelo repetidamente).

## Mejoras funcionales

- **Modelo `large-v3` está en las `choices` del CLI pero no en el cache local** — no es un bug, solo confirma que se descarga on-demand; podría valer la pena advertir en el README que `large-v3` es sustancialmente más pesado/lento en CPU que `medium`.
- **Sin manejo de reintentos ni checksum en la descarga de modelos.** Si la descarga de Hugging Face se corta a mitad (común en conexiones lentas, el escenario que el propio README anticipa), no hay validación explícita de integridad antes de usar el modelo.
- **No hay forma de listar/limpiar modelos cacheados desde el CLI.** Todo pasa por manipular `cache/` manualmente.
- **Sin flag para forzar CPU threads/workers óptimos según el hardware** — los defaults (`cpu_threads=2`, `num_workers=2`) son conservadores; en el README podría sugerirse cómo ajustar esto en un equipo con más núcleos para acelerar `medium`/`large-v3`.
- **No hay progreso de traducción** — el paso de transcripción imprime progreso cada N segmentos (`--progress`), pero `translate_segments` no imprime nada hasta terminar el batch completo, lo cual puede parecer "colgado" en audios largos.

## Documentación / onboarding

- Los instaladores (`install-windows.sh`, `install-mac.sh`) agregan el usuario al grupo `docker` y crean un wrapper global en `/usr/local/bin/audio2text`, pero el README solo documenta el flujo vía `docker compose run` directo — no menciona el comando global `audio2text` que el propio instalador crea. Vale la pena unificar cuál es el flujo "canónico" a documentar.
- No hay una sección de "Desinstalación" ni de cómo liberar espacio en disco (borrar `cache/`, imágenes Docker, etc.) una vez terminado el curso/proyecto.

## Post-procesamiento de transliteración con LLM

- **Agregar un paso opcional de limpieza de la transcripción vía LLM**, como etapa posterior a `faster-whisper` y antes (o en paralelo) de la traducción. Prueba de concepto manual ya hecha sobre `outputs/17-07-2026 09.54/17-07-2026 09.54_es.txt` → [17-07-2026 09.54_es_revisado.txt](outputs/17-07-2026%2009.54/17-07-2026%2009.54_es_revisado.txt), que muestra el criterio a seguir:
  - Corrige errores fonéticos claros (homófonos, nombres propios reconocibles por contexto — p. ej. "Necki"→"Nequi", "cotas"→"cuotas", "pasesal"→"paz y salvo", "ahogados"→"abogados").
  - Deja intactos y marcados (`[??]` + timestamp) los fragmentos que no se pueden reconstruir con confianza, en vez de inventar contenido — en esa prueba quedaron **9 fragmentos** así, que requieren re-escuchar el audio.
- Decisiones de diseño pendientes para implementarlo como feature real (no solo prueba manual):
  - ¿Se ejecuta local (algún modelo vía `transformers`, sumando otra descarga de modelo) o llamando a una API externa de LLM? Esto último rompería la promesa del README de que "todo el procesamiento ocurre en tu computador" — hay que decidir y documentarlo explícitamente si se opta por API externa.
  - ¿Cómo se conserva la alineación con los timestamps del `.srt` cuando el LLM reescribe texto (agrega/quita palabras)? El `.srt`/`.json` actual asume que el texto de cada segmento no cambia de longitud/sentido.
  - Definir el criterio de "no inventar" como reglas verificables (ej. no tocar texto fuera de una lista de correcciones fonéticas conocidas + nombres propios del dominio) para que el resultado sea reproducible y no dependa de qué tan "creativo" esté el LLM en cada corrida.
  - Exponer como flag opcional en el CLI (p. ej. `--polish` o `--llm-cleanup`), no como comportamiento por defecto, dado que introduce una dependencia adicional y tiempo de proceso extra.
