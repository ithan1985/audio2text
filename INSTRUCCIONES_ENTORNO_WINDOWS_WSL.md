# Guía de Instalación de Entorno de Desarrollo en Windows con WSL (Ubuntu)

Esta guía te mostrará paso a paso cómo configurar un entorno de desarrollo completo en tu máquina Windows utilizando el Subsistema de Windows para Linux (WSL) con la distribución de Ubuntu.

## Requisitos Previos

- Windows 11.
- Acceso a internet.
- Privilegios de administrador en tu máquina.

---

## Paso 1: Instalar WSL y Ubuntu

WSL te permite ejecutar un entorno GNU/Linux directamente en Windows, sin la sobrecarga de una máquina virtual tradicional.

1.  **Abre PowerShell o el Símbolo del sistema (CMD) como Administrador.**
    - Haz clic derecho en el menú Inicio y selecciona "Windows PowerShell (Administrador)" o "Terminal (Administrador)".

2.  **Ejecuta el siguiente comando para instalar WSL y Ubuntu:**
    Este comando se encargará de descargar e instalar la última versión de WSL y la distribución de Ubuntu por defecto.

    ```bash
    wsl --install
    ```

3.  **Reinicia tu computadora.**
    Una vez que el proceso termine, se te pedirá que reinicies tu sistema para completar la instalación.

4.  **Configura tu usuario de Ubuntu.**
    Después de reiniciar, Ubuntu se iniciará automáticamente. Si no lo hace, búscalo en el menú Inicio y ábrelo. La primera vez que se ejecute, te pedirá que crees un nombre de usuario y una contraseña.

    > **Importante:** Esta contraseña será la que usarás para comandos `sudo` (comandos de administrador) dentro de Ubuntu. ¡No la olvides!

Para más detalles, puedes consultar la documentación oficial de Microsoft sobre la instalación de WSL.

---

## Paso 2: Actualizar tu Entorno de Ubuntu

Una vez dentro de tu terminal de Ubuntu, es una buena práctica actualizar la lista de paquetes y el software instalado.

```bash
# Actualiza la lista de paquetes disponibles y sus versiones
sudo apt update

# Instala las actualizaciones de los paquetes
sudo apt upgrade -y
```

---

## Paso 3: Instalar Herramientas de Desarrollo Esenciales y Git

El paquete `build-essential` contiene herramientas fundamentales para la compilación de software (como `gcc`, `g++` y `make`). Git es el sistema de control de versiones más popular.

```bash
sudo apt install build-essential git -y
```

---

## Paso 4: Instalar Node.js y npm usando nvm

`nvm` (Node Version Manager) es la forma recomendada de instalar Node.js y npm, ya que te permite cambiar fácilmente entre diferentes versiones de Node.js.

1.  **Instala nvm.**
    Ejecuta el siguiente comando para descargar y ejecutar el script de instalación de `nvm`.

    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    ```

2.  **Carga nvm en tu sesión actual.**
    Para empezar a usar `nvm` sin tener que cerrar y abrir la terminal, ejecuta:

    ```bash
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    ```

3.  **Instala la última versión LTS (Long-Term Support) de Node.js.**
    LTS es la versión recomendada para la mayoría de los usuarios por su estabilidad.

    ```bash
    nvm install --lts
    ```

4.  **Verifica la instalación.**
    
    ```bash
    node -v
    npm -v
    ```

Para más información, visita el repositorio oficial de nvm en GitHub.

---

## Paso 5: Integración con Visual Studio Code

VS Code tiene una integración excepcional con WSL, permitiéndote editar archivos que están en tu sistema de archivos de Linux con la comodidad de una GUI en Windows.

1.  **Instala VS Code en Windows.**
    Si aún no lo tienes, descárgalo e instálalo desde la página oficial de Visual Studio Code.

2.  **Instala la extensión "WSL" en VS Code.**
    - Abre VS Code.
    - Ve a la pestaña de Extensiones (Ctrl+Shift+X).
    - Busca `WSL` y haz clic en "Instalar" en la extensión publicada por Microsoft.

3.  **Abre proyectos desde tu terminal de Ubuntu.**
    Ahora puedes navegar a la carpeta de un proyecto dentro de tu terminal de Ubuntu y abrirla directamente en VS Code ejecutando:

    ```bash
    code .
    ```

    La primera vez que hagas esto, VS Code se configurará automáticamente para conectarse a tu entorno WSL.

---

¡Felicidades! Ahora tienes un potente entorno de desarrollo basado en Linux configurado en tu máquina Windows. Puedes instalar otras herramientas que necesites (como bases de datos, Docker, etc.) directamente desde tu terminal de Ubuntu usando `apt`.