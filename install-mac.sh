#!/bin/bash

set -e

echo "======================================"
echo " AUDIO2TEXT INSTALLER - MAC"
echo " Instalacion automatica para estudiantes"
echo "======================================"

PROJECT_DIR="$(pwd)"

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
brew install git curl wget zip unzip ffmpeg || true

echo ""
echo "[4/7] Verificando Docker..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker no esta instalado."
  echo "Instala Docker Desktop para Mac:"
  echo "https://www.docker.com/products/docker-desktop/"
  exit 1
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
  echo "Docker esta instalado pero no esta corriendo."
  echo "Abre Docker Desktop y espera a que indique que esta activo."
  echo "Luego vuelve a ejecutar:"
  echo "./install_mac.sh"
  exit 1
fi

echo ""
echo "[7/7] Preparando proyecto..."

mkdir -p audios
mkdir -p outputs
mkdir -p cache

echo ""
echo "Construyendo contenedor..."
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