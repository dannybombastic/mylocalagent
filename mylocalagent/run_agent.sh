#!/bin/bash
set -e

# Activa el entorno virtual
if [ -d "./venv" ]; then
    source ./venv/bin/activate
else
    echo "El entorno virtual ./venv no existe. Por favor, ejecuta primero setup_venv.sh"
    exit 1
fi

# Inicia el agente
python mylocalagent/agent.py
