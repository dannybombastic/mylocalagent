#!/bin/bash
set -e

# Activa el entorno virtual desde el path correcto
if [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo "El entorno virtual ../venv no existe. Por favor, ejecuta primero setup_venv.sh desde el directorio mylocalagent/"
    exit 1
fi

# Inicia el agente (asumiendo ejecución desde mylocalagent/)
python agent.py
