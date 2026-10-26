#!/bin/bash
set -euo pipefail

# Resolve paths relative to this script, not the caller's current directory.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
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

# Instala el MCP oficial de Azure DevOps (https://github.com/microsoft/azure-devops-mcp)
# dentro del propio proyecto (node_modules/), para que agent.py no dependa de ningún
# clon externo fuera del repo. Node es opcional: si falta, agent.py sigue funcionando
# sin las herramientas de Azure DevOps.
PACKAGE_JSON="$SCRIPT_DIR/package.json"
if [ -f "$PACKAGE_JSON" ]; then
    if command -v npm >/dev/null 2>&1; then
        echo "Instalando el MCP de Azure DevOps (npm) en $SCRIPT_DIR/node_modules..."
        (cd "$SCRIPT_DIR" && npm install --no-audit --no-fund)
        echo "MCP de Azure DevOps instalado."
    else
        echo "Aviso: no se encontró 'npm' en el PATH. Instala Node.js si quieres que el" >&2
        echo "agente use las herramientas de Azure DevOps (ver README.md)." >&2
    fi
fi
