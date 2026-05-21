#!/bin/bash

set -e

echo "======================================"
echo " AUDIO2TEXT INSTALLER"
echo " Instalacion automatica para estudiantes"
echo "======================================"

PROJECT_DIR="$(pwd)"

echo ""
echo "[1/9] Verificando sistema operativo..."

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este instalador esta diseñado para Ubuntu / WSL."
  echo "En Mac instala Docker Desktop y ejecuta docker compose build manualmente."
  exit 1
fi

echo ""
echo "[2/9] Actualizando Ubuntu..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "[3/9] Instalando herramientas basicas..."
sudo apt install -y \
git \
curl \
wget \
zip \
unzip \
ca-certificates \
gnupg \
lsb-release \
ffmpeg

echo ""
echo "[4/9] Instalando Docker oficial..."

sudo install -m 0755 -d /etc/apt/keyrings

if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
fi

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y \
docker-ce \
docker-ce-cli \
containerd.io \
docker-buildx-plugin \
docker-compose-plugin

echo ""
echo "[5/9] Iniciando Docker..."
sudo service docker start || true

echo ""
echo "[6/9] Configurando permisos Docker..."
sudo usermod -aG docker "$USER"

echo ""
echo "[7/9] Creando carpetas necesarias..."

mkdir -p audios
mkdir -p outputs
mkdir -p cache

echo ""
echo "[8/9] Creando comando global audio2text..."

sudo tee /usr/local/bin/audio2text > /dev/null <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
docker compose run --rm audio2text "\$@"
EOF

sudo chmod +x /usr/local/bin/audio2text

echo ""
echo "[9/9] Construyendo contenedor..."

if docker ps >/dev/null 2>&1; then
  docker compose build
else
  sudo docker compose build
fi

echo ""
echo "======================================"
echo " INSTALACION COMPLETADA"
echo "======================================"

echo ""
echo "IMPORTANTE:"
echo "Cierra Ubuntu WSL y vuelve a abrirlo para activar permisos Docker."
echo ""

echo "Luego verifica Docker con:"
echo ""
echo "docker ps"
echo ""

echo "Si Docker no esta activo, ejecuta:"
echo ""
echo "sudo service docker start"
echo ""

echo "Luego puedes ejecutar:"
echo ""
echo 'audio2text "audios/audio1.m4a" -l en --translate-to es -m small --vad'
echo ""

echo "Resultados generados en:"
echo "./outputs/"
echo ""