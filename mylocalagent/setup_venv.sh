#!/bin/bash
set -e

# Crea entorno virtual en la raíz del repo
if [ ! -d "./venv" ]; then
    echo "Creando entorno virtual en ./venv..."
    python3 -m venv ./venv
else
    echo "El entorno virtual ./venv ya existe."
fi

# Activa el entorno virtual
source ./venv/bin/activate

# Actualiza pip y wheel
pip install --upgrade pip wheel

# Instala dependencias del proyecto
if [ -f "mylocalagent/requirements.txt" ]; then
    pip install -r mylocalagent/requirements.txt
else
    echo "No se encontró requirements.txt en mylocalagent/, saltando instalación de paquetes."
fi

echo "Entorno virtual instalado y dependencias listas."
