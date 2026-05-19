#!/bin/bash

set -e

echo "======================================"
echo " AUDIO2TEXT INSTALLER"
echo " Instalacion automatica para estudiantes"
echo "======================================"

echo ""
echo "[1/7] Actualizando Ubuntu..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "[2/7] Instalando herramientas basicas..."
sudo apt install -y \
git \
curl \
wget \
zip \
unzip \
ca-certificates \
gnupg \
lsb-release

echo ""
echo "[3/7] Instalando Docker oficial..."

sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

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
echo "[4/7] Iniciando Docker..."
sudo service docker start || true

echo ""
echo "[5/7] Configurando permisos Docker..."
sudo usermod -aG docker $USER

echo ""
echo "[6/7] Creando comando global audio2text..."

sudo tee /usr/local/bin/audio2text > /dev/null <<EOF
#!/bin/bash

cd $PWD
docker compose run --rm audio2text "\$@"
EOF

sudo chmod +x /usr/local/bin/audio2text

echo ""
echo "[7/7] Construyendo contenedor..."
docker compose build

echo ""
echo "======================================"
echo " INSTALACION COMPLETADA"
echo "======================================"

echo ""
echo "IMPORTANTE:"
echo "Cierra Ubuntu y vuelve a abrirlo."
echo ""

echo "Luego puedes ejecutar:"
echo ""
echo 'audio2text "audios/audio1.m4a"'
echo ""
echo "o"
echo ""
echo 'audio2text "audios/audio2.m4a"'
echo ""

echo "Resultados generados en:"
echo "./outputs/"
echo ""