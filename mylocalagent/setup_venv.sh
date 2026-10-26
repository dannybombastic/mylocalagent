#!/bin/bash
set -euo pipefail

# Resolve paths relative to this script, not the caller's current directory.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: no se encontró requirements.txt junto al script: $REQUIREMENTS_FILE" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Usando entorno virtual existente en $VENV_DIR."
fi

PYTHON="$VENV_DIR/bin/python"

"$PYTHON" -m pip install --upgrade pip wheel
"$PYTHON" -m pip install -r "$REQUIREMENTS_FILE"

echo "Entorno virtual preparado y dependencias instaladas."
