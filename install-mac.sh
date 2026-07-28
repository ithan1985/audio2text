#!/bin/bash

set -e

echo "======================================"
echo " AUDIO2TEXT INSTALLER - MAC"
echo " Instalacion automatica para estudiantes"
echo "======================================"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "[1/7] Verificando macOS..."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este instalador es solo para macOS."
  exit 1
fi

echo ""
echo "[2/7] Verificando Homebrew..."

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew no esta instalado."
  echo "Instalalo con:"
  echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi

echo ""
echo "[3/7] Instalando herramientas basicas..."

brew update
brew install git curl wget zip unzip ffmpeg

echo ""
echo "[4/7] Instalando Docker Desktop..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker no encontrado. Instalando via Homebrew..."
  brew install --cask docker
  echo ""
  echo "======================================"
  echo " ACCION REQUERIDA"
  echo "======================================"
  echo ""
  echo "Docker Desktop fue instalado pero necesitas abrirlo"
  echo "antes de continuar:"
  echo ""
  echo "  1. Abre el Launchpad (el icono de cohete en el Dock)"
  echo "  2. Busca y abre 'Docker'"
  echo "  3. Espera hasta ver el icono de ballena en la barra"
  echo "     superior de tu pantalla"
  echo "  4. Vuelve a esta ventana y ejecuta de nuevo:"
  echo "     ./install-mac.sh"
  echo ""
  echo "Si no puedes usar Docker en este Mac, hay una alternativa sin Docker:"
  echo "  ./install-mac-native.sh   (o: make mac-native)"
  echo ""
  exit 0
fi

echo "Docker detectado:"
docker --version

echo ""
echo "[5/7] Verificando Docker Compose..."

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose no esta disponible."
  echo "Abre o actualiza Docker Desktop."
  exit 1
fi

docker compose version

echo ""
echo "[6/7] Verificando si Docker esta corriendo..."

if ! docker ps >/dev/null 2>&1; then
  echo ""
  echo "======================================"
  echo " ACCION REQUERIDA"
  echo "======================================"
  echo ""
  echo "Docker esta instalado pero no esta corriendo."
  echo ""
  echo "  1. Abre el Launchpad (el icono de cohete en el Dock)"
  echo "  2. Busca y abre 'Docker'"
  echo "  3. Espera hasta ver el icono de ballena en la barra"
  echo "     superior de tu pantalla"
  echo "  4. Vuelve a esta ventana y ejecuta de nuevo:"
  echo "     ./install-mac.sh"
  echo ""
  echo "Si no puedes usar Docker en este Mac, hay una alternativa sin Docker:"
  echo "  ./install-mac-native.sh   (o: make mac-native)"
  echo ""
  exit 1
fi

echo ""
echo "[7/7] Preparando proyecto..."

mkdir -p "$PROJECT_DIR/audios"
mkdir -p "$PROJECT_DIR/outputs"
mkdir -p "$PROJECT_DIR/cache"

echo ""
echo "Construyendo contenedor..."
cd "$PROJECT_DIR"
docker compose build

echo ""
echo "Creando comando global audio2text..."

sudo tee /usr/local/bin/audio2text > /dev/null <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
docker compose run --rm audio2text "\$@"
EOF

sudo chmod +x /usr/local/bin/audio2text

echo ""
echo "======================================"
echo " INSTALACION COMPLETADA EN MAC"
echo "======================================"
echo ""
echo "Puedes ejecutar:"
echo ""
echo 'audio2text "audios/audio1.m4a" -l en --translate-to es -m small --vad'
echo ""
echo "Resultados generados en:"
echo "./outputs/"
echo ""
