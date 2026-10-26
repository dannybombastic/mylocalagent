#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
AGENT_SCRIPT="$SCRIPT_DIR/agent.py"

if [ ! -d "$VENV_DIR" ]; then
    echo "El entorno virtual $VENV_DIR no existe. Por favor, ejecuta primero setup_venv.sh desde el directorio mylocalagent."
    exit 1
fi

source "$VENV_DIR/bin/activate"

echo "Ejecutando agente desde $AGENT_SCRIPT"
python "$AGENT_SCRIPT"
