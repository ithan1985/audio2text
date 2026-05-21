# audio2text

Herramienta para transcribir y traducir archivos de audio o video a texto, sin conexión a internet y sin costo por uso. Desarrollada como PoC para la asignatura **Gestión del Conocimiento y Transferencia Tecnológica** — Universidad Militar Nueva Granada.

---

## Qué hace esta aplicación

- Toma un archivo de audio o video (mp3, m4a, mp4, wav, etc.)
- Lo transcribe a texto usando inteligencia artificial local
- Genera tres archivos de salida:
  - `.txt` — texto plano
  - `.srt` — subtítulos con marcas de tiempo
  - `.json` — datos estructurados
- Opcionalmente traduce el resultado a otro idioma

Todo el procesamiento ocurre en tu computador. No se envía información a ningún servidor externo.

---

## Requisitos previos

| Sistema operativo | Requisito |
|---|---|
| Windows | Windows 10 u 11 (64 bits) |
| Mac | macOS 12 o superior, chip Intel o Apple Silicon |

No se requiere experiencia en programación. Sigue los pasos en orden.

---

## Instalación en Windows

### Paso 1 — Activar WSL e instalar Ubuntu

1. Presiona `Windows + S`, escribe **PowerShell**
2. Haz clic derecho sobre PowerShell y elige **"Ejecutar como administrador"**
3. Copia y pega este comando, luego presiona Enter:

```
wsl --install
```

4. Cuando termine, **reinicia tu computador**
5. Al reiniciar, se abrirá una ventana de Ubuntu pidiendo que crees un usuario y contraseña — escoge los que quieras y anótalos

> Si Ubuntu no se abre solo, búscalo en el menú Inicio como "Ubuntu".

---

### Paso 2 — Actualizar Ubuntu

Dentro de la ventana de Ubuntu, copia y pega:

```bash
sudo apt update && sudo apt upgrade -y
```

Te pedirá la contraseña que creaste en el paso anterior. Escríbela y presiona Enter (no verás los caracteres mientras escribes, eso es normal).

---

### Paso 3 — Instalar Git

```bash
sudo apt install git -y
```

---

### Paso 4 — Clonar el repositorio

```bash
git clone https://github.com/ithan1985/audio2text.git
cd audio2text
```

---

### Paso 5 — Dar permisos al instalador

```bash
chmod +x install-windows.sh
```

---

### Paso 6 — Ejecutar el instalador

```bash
./install-windows.sh
```

Este paso instala Docker y todas las dependencias necesarias. Puede tardar varios minutos.

---

### Paso 7 — Cerrar y reabrir Ubuntu

> **Este paso es obligatorio.** Sin él, el siguiente comando fallará.

Cierra la ventana de Ubuntu completamente y vuelve a abrirla desde el menú Inicio.

---

### Paso 8 — Probar la instalación

```bash
cd audio2text
docker compose run --rm audio2text "audios/audio1.m4a" -l es --translate-to en -m small --vad
```

La primera vez descargará los modelos de IA (puede tardar unos minutos según tu conexión). Las siguientes veces será mucho más rápido.

Los resultados quedarán en la carpeta `outputs/`.

---

## Instalación en Mac

### Paso 1 — Abrir la Terminal

Presiona `Command + Espacio`, escribe **Terminal** y presiona Enter.

---

### Paso 2 — Instalar Homebrew

Homebrew es un gestor de aplicaciones para Mac. Si ya lo tienes instalado, salta al Paso 3.

Copia y pega este comando completo:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Sigue las instrucciones en pantalla. Te pedirá tu contraseña de Mac.

> **Usuarios con chip Apple Silicon (M1/M2/M3/M4):** al terminar, Homebrew mostrará dos comandos adicionales para agregar brew al PATH. Ejecútalos antes de continuar.

---

### Paso 3 — Instalar Git

```bash
brew install git
```

---

### Paso 4 — Clonar el repositorio

```bash
git clone https://github.com/ithan1985/audio2text.git
cd audio2text
```

---

### Paso 5 — Dar permisos al instalador

```bash
chmod +x install-mac.sh
```

---

### Paso 6 — Ejecutar el instalador

```bash
./install-mac.sh
```

Si Docker Desktop no está instalado, el script lo instalará automáticamente y te pedirá que lo abras antes de continuar.

**Cuando el script te indique que abras Docker:**
1. Abre el **Launchpad** (ícono de cohete en el Dock)
2. Busca y abre **Docker**
3. Espera hasta ver el ícono de ballena 🐋 en la barra superior de tu pantalla
4. Vuelve a la Terminal y ejecuta nuevamente:

```bash
./install-mac.sh
```

---

### Paso 7 — Probar la instalación

```bash
docker compose run --rm audio2text "audios/audio1.m4a" -l es --translate-to en -m small --vad
```

La primera vez descargará los modelos de IA (puede tardar unos minutos). Los resultados quedarán en la carpeta `outputs/`.

---

## Cómo usar tus propios archivos de audio

1. Copia tu archivo de audio (mp3, m4a, mp4, wav, etc.) dentro de la carpeta `audios/`

   - **Windows:** la carpeta se encuentra en `\\wsl$\Ubuntu\home\TU_USUARIO\audio2text\audios\`
     Puedes abrirla desde el Explorador de archivos pegando esa ruta en la barra de direcciones.
   - **Mac:** la carpeta se encuentra en `~/audio2text/audios/`

2. Ejecuta el comando reemplazando `mi_audio.mp3` con el nombre exacto de tu archivo:

```bash
docker compose run --rm audio2text "audios/mi_audio.mp3" -l es --translate-to en -m small --vad
```

---

## Opciones del comando

| Opción | Qué hace | Ejemplo |
|---|---|---|
| `-l` | Idioma del audio | `-l es` (español), `-l en` (inglés) |
| `--translate-to` | Idioma al que traducir | `--translate-to en` |
| `-m` | Tamaño del modelo (precisión vs. velocidad) | `-m small` |
| `--vad` | Mejora la segmentación en audios con ruido | `--vad` |
| `--start` | Segundo de inicio del recorte | `--start 60` (desde el minuto 1) |
| `--duration` | Duración en segundos a procesar | `--duration 30` (solo 30 segundos) |

**Modelos disponibles** (de más rápido a más preciso):
`tiny` → `base` → `small` → `medium` → `large-v3`

Para la mayoría de usos académicos, `small` ofrece un buen balance.

**Idiomas soportados para traducción:**
`es` (español), `en` (inglés), `fr` (francés), `de` (alemán), `it` (italiano), `pt` (portugués), `zh` (chino), `ja` (japonés), `ko` (coreano), `ru` (ruso), `ar` (árabe)

---

## Dónde encontrar los resultados

Los archivos de salida se generan en:

```
audio2text/
└── outputs/
    └── nombre_del_audio/
        ├── nombre_del_audio_es.txt      ← transcripción en español
        ├── nombre_del_audio_es.srt      ← subtítulos con tiempos
        ├── nombre_del_audio_es.json     ← datos estructurados
        ├── nombre_del_audio_es-en.txt   ← traducción al inglés
        ├── nombre_del_audio_es-en.srt
        └── nombre_del_audio_es-en.json
```

---

## Ejemplos de comandos

**Transcribir audio en español y traducir al inglés:**
```bash
docker compose run --rm audio2text "audios/audio1.m4a" -l es --translate-to en -m small --vad
```

**Transcribir audio en inglés (sin traducción):**
```bash
docker compose run --rm audio2text "audios/entrevista.mp3" -l en -m small --vad
```

**Detección automática del idioma:**
```bash
docker compose run --rm audio2text "audios/grabacion.m4a" -l "" -m small --vad
```

**Procesar solo los primeros 30 segundos (útil para pruebas):**
```bash
docker compose run --rm audio2text "audios/historia.mp3" -l en --duration 30 --translate-to es -m small
```

**Procesar desde el minuto 1 durante 30 segundos:**
```bash
docker compose run --rm audio2text "audios/historia.mp3" -l en --start 60 --duration 30 --translate-to es -m small
```

---

## Solución de problemas frecuentes

**"docker: command not found"**
→ En Windows: cerraste Ubuntu después de la instalación? Es obligatorio. Ciérralo y ábrelo de nuevo.
→ En Mac: Docker Desktop está abierto? Busca el ícono de ballena en la barra superior.

**El comando tarda mucho la primera vez**
→ Normal. Está descargando el modelo de IA (~500MB para `small`). Las siguientes ejecuciones son inmediatas.

**"No existe el archivo"**
→ Verifica que el nombre del archivo en el comando coincide exactamente con el nombre real, incluyendo la extensión.

**El texto transcrito tiene muchos errores**
→ Prueba con un modelo más grande: cambia `-m small` por `-m medium`.
→ Activa `--vad` si el audio tiene ruido de fondo.

---

## Información del proyecto

- **Asignatura:** Gestión del Conocimiento y Transferencia Tecnológica
- **Institución:** Universidad Militar Nueva Granada
- **Motor de transcripción:** [faster-whisper](https://github.com/Systran/faster-whisper)
- **Traducción:** [NLLB-200](https://huggingface.co/facebook/nllb-200-distilled-600M) de Meta AI vía ctranslate2 (offline, sin torch)
- **Procesamiento:** 100% local, sin internet durante la transcripción y traducción

---

## Licencia

Copyright (c) 2026 Jonathan L Gutierrez V. Todos los derechos reservados.

Uso libre para fines académicos, educativos y de investigación con atribución al autor.
Prohibido el uso comercial sin autorización escrita previa.

[Ver texto completo](LICENSE)
- **Autor:** Jonathan Leonel Gutierrez Villamarin

