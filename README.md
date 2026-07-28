# KeyPresser

KeyPresser es una aplicación desarrollada en Python para configurar y ejecutar pulsaciones automáticas de teclado con intervalos independientes.

El proyecto se encuentra actualmente en desarrollo.

## Funcionalidades actuales

- Interfaz gráfica.
- Activación individual de teclas mediante checkbox.
- Intervalo independiente por tecla en milisegundos.
- Teclas disponibles:
  - E
  - R
  - F
  - 1 al 9
  - 0
- Selección de proceso objetivo.
- Modo de funcionamiento con la aplicación objetivo en primer plano.
- Modo experimental de envío de teclas en segundo plano.
- Detención automática si el proceso objetivo se cierra.

## Estructura del proyecto

```text
KeyPresser/
├── main.py
├── gui.py
├── engine.py
├── requirements.txt
├── README.md
└── .gitignore
```

### main.py

Punto de entrada de la aplicación.

Se encarga de iniciar la interfaz gráfica.

### gui.py

Contiene la interfaz gráfica y la interacción con el usuario:

- Selector de aplicación objetivo.
- Checkboxes de teclas.
- Configuración de intervalos.
- Botones de iniciar y detener.
- Estado de ejecución.

### engine.py

Contiene el motor de funcionamiento:

- Gestión de procesos.
- Detección de ventanas.
- Temporizadores de las teclas.
- Envío de pulsaciones.
- Control del proceso objetivo.

## Requisitos

- Python 3
- Windows 11 para las funcionalidades Win32 actuales.

Dependencias principales:

- pynput
- psutil
- pywin32

Las versiones utilizadas están disponibles en `requirements.txt`.

## Instalación

Clonar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd KeyPresser
```

Crear un entorno virtual:

```bash
python -m venv .venv
```

### Windows PowerShell

Activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Ejecución

Con el entorno virtual activado:

```powershell
python main.py
```

## Estado del proyecto

KeyPresser está en desarrollo y su arquitectura, interfaz y funcionalidades pueden cambiar.

Actualmente el proyecto está orientado a Windows. La compatibilidad con Linux podrá estudiarse más adelante separando las implementaciones específicas del sistema operativo.

## Aviso

El modo de segundo plano depende de cómo la aplicación objetivo procese la entrada de teclado y puede no funcionar con todas las aplicaciones o juegos.