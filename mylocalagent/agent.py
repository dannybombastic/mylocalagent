# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
# Integración MCP: https://strandsagents.com/docs/user-guide/sdk/tools/mcp-tools/

import os
import shutil

from system_instructions import SYSTEM_INSTRUCTIONS

from strands import Agent

# Ruta local del servidor MCP oficial de Azure DevOps (github.com/microsoft/azure-devops-mcp),
# el mismo binario que usa VS Code (ver ~/.config/Code/User/mcp.json). Se puede
# sobreescribir con la variable de entorno ADO_MCP_SERVER_PATH si vive en otra ruta.
ADO_MCP_SERVER_PATH = os.environ.get(
    "ADO_MCP_SERVER_PATH",
    os.path.expanduser("~/Documents/azure-devops-mcp/dist/index.js"),
)


def build_ado_mcp_client():
    """Crea el cliente MCP (stdio) del servidor oficial de Azure DevOps.

    Devuelve None (con un aviso) si falta algún requisito, para que el agente
    siga funcionando sin herramientas de Azure DevOps en vez de fallar.
    """
    org = os.environ.get("ADO_ORG")
    pat = os.environ.get("AZURE_DEVOPS_EXT_PAT")

    if not (org and pat):
        print(
            "Aviso: faltan ADO_ORG y/o AZURE_DEVOPS_EXT_PAT en el entorno; "
            "el agente no tendrá herramientas MCP de Azure DevOps."
        )
        return None
    if not shutil.which("node"):
        print("Aviso: no se encontró 'node' en el PATH; no se puede iniciar el MCP de Azure DevOps.")
        return None
    if not os.path.isfile(ADO_MCP_SERVER_PATH):
        print(
            f"Aviso: no se encontró el servidor MCP de Azure DevOps en {ADO_MCP_SERVER_PATH}; "
            "define ADO_MCP_SERVER_PATH si está en otra ruta."
        )
        return None

    from mcp import StdioServerParameters, stdio_client
    from strands.tools.mcp import MCPClient

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="node",
                args=[ADO_MCP_SERVER_PATH, org, "--authentication", "env"],
                env=dict(os.environ),
            )
        )
    )


if __name__ == "__main__":
    # Import dinámico sólo si Ollama realmente está instalado y operando.
    use_ollama = False
    try:
        from strands.models.ollama import OllamaModel
        import requests
        # Probar si Ollama server responde...
        response = requests.get("http://localhost:11434")
        if response.ok:
            use_ollama = True
    except Exception:
        use_ollama = False

    # El MCPClient implementa ToolProvider: pasándolo en `tools=` el Agent gestiona
    # solo la conexión/desconexión del servidor MCP (ver doc oficial de MCP tools).
    tools = []
    ado_mcp_client = build_ado_mcp_client()
    if ado_mcp_client is not None:
        tools.append(ado_mcp_client)
        print("Herramientas MCP de Azure DevOps conectadas.")

    if use_ollama:
        # num_ctx por defecto en Ollama es 4096 tokens. Las ~70 tools del MCP de Azure
        # DevOps ocupan sólo en sus definiciones ~18k tokens, así que con el valor por
        # defecto el modelo ni siquiera llega a "ver" la mayoría y acaba alucinando que
        # no existen. Se amplía para que quepan tools + system prompt + conversación.
        model = OllamaModel(
            host="http://localhost:11434",
            model_id="qwen3.8:latest",
            options={"num_ctx": 24576},
        )
        agent = Agent(model=model, system_prompt=SYSTEM_INSTRUCTIONS, tools=tools)
    else:
        print("¡Ollama no está disponible! Usando sólo el core del agente Strands sin modelo local Ollama. "
              "Si ves errores de AWS/Bedrock, asegúrate de que Ollama esté activo y accesible localmente.")
        agent = Agent(system_prompt=SYSTEM_INSTRUCTIONS, tools=tools)

    print("Agente DevOps local listo. Escribe tu mensaje y pulsa Enter.")
    print("Comandos: 'salir', 'exit' o 'quit' para terminar; Ctrl+C también sale.\n")

    # El objeto `agent` acumula el historial de conversación en self.messages,
    # así que reutilizarlo en cada vuelta del bucle mantiene el contexto del chat.
    while True:
        try:
            user_input = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo...")
            break

        if not user_input:
            continue
        if user_input.lower() in {"salir", "exit", "quit"}:
            print("Saliendo...")
            break

        # No envolver en print(): el Agent usa por defecto un PrintingCallbackHandler
        # que ya va imprimiendo (streaming) la respuesta por consola (ver doc oficial).
        agent(user_input)
