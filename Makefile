.PHONY: help win mac mac-native build run run-native

help:
	@echo "audio2text - targets disponibles:"
	@echo "  make win        - instala audio2text en Ubuntu/WSL (install-windows.sh)"
	@echo "  make mac        - instala audio2text en macOS con Docker (install-mac.sh)"
	@echo "  make mac-native - instala audio2text en macOS SIN Docker, con venv (install-mac-native.sh)"
	@echo "  make build      - reconstruye la imagen Docker"
	@echo "  make run ARGS='audios/audio1.mp3 -l es --translate-to en -m small --vad'"
	@echo "                  - corre la transcripcion via Docker"
	@echo "  make run-native ARGS='audios/audio1.mp3 -l es --translate-to en -m small --vad'"
	@echo "                  - corre la transcripcion via el venv de mac-native"

win:
	chmod +x install-windows.sh
	./install-windows.sh

mac:
	chmod +x install-mac.sh
	./install-mac.sh

mac-native:
	chmod +x install-mac-native.sh
	./install-mac-native.sh

build:
	docker compose build

run:
	docker compose run --rm audio2text $(ARGS)

run-native:
	.venv/bin/python3 transcribe.py -o outputs $(ARGS)
