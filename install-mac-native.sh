#!/bin/bash

set -e

echo "======================================"
echo " AUDIO2TEXT INSTALLER - MAC (SIN DOCKER)"
echo " Instalacion nativa con Python venv"
echo "======================================"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "[1/5] Verificando macOS..."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este instalador es solo para macOS."
  exit 1
fi

echo ""
echo "[2/5] Verificando Homebrew..."

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew no esta instalado."
  echo "Instalalo con:"
  echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi

echo ""
echo "[3/5] Instalando ffmpeg y python3..."

brew update
brew install ffmpeg python3

echo ""
echo "[4/5] Creando entorno virtual (.venv) e instalando dependencias..."

cd "$PROJECT_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo ""
echo "[5/5] Preparando carpetas del proyecto..."

mkdir -p "$PROJECT_DIR/audios"
mkdir -p "$PROJECT_DIR/outputs"
mkdir -p "$PROJECT_DIR/cache"

echo ""
echo "======================================"
echo " INSTALACION NATIVA COMPLETADA"
echo "======================================"
echo ""
echo "Esta instalacion NO usa Docker: corre transcribe.py directo con el"
echo "Python del sistema, dentro del entorno virtual .venv/"
echo ""
echo "Para usarla, activa el entorno y llama a transcribe.py indicando -o outputs"
echo "(a diferencia de Docker, aqui no hay un outdir por defecto):"
echo ""
echo "source .venv/bin/activate"
echo 'python3 transcribe.py "audios/audio1.mp3" -l es --translate-to en -m small --vad -o outputs'
echo ""
echo "O en un solo paso, sin activar manualmente:"
echo ""
echo 'make run-native ARGS="audios/audio1.mp3 -l es --translate-to en -m small --vad"'
echo ""
echo "Resultados generados en:"
echo "./outputs/"
echo ""
