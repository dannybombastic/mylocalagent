# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
# Integración MCP: https://strandsagents.com/docs/user-guide/sdk/tools/mcp-tools/

import os
import re
import shutil

from system_instructions import SYSTEM_INSTRUCTIONS

from strands import Agent

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Servidor MCP oficial de Azure DevOps (github.com/microsoft/azure-devops-mcp),
# instalado dentro del propio proyecto por setup_venv.sh (ver package.json), para
# que el repo sea autocontenido. Se puede sobreescribir con ADO_MCP_SERVER_PATH
# si prefieres apuntar a otra instalación.
ADO_MCP_SERVER_PATH = os.environ.get(
    "ADO_MCP_SERVER_PATH",
    os.path.join(PROJECT_DIR, "node_modules", "@azure-devops", "mcp", "dist", "index.js"),
)

# El servidor expone ~70 tools (work items, repos, pipelines, wikis, test plans,
# Advanced Security...) cuyas definiciones por sí solas ocupan ~20k tokens en CADA
# llamada al modelo. En conversaciones de varias rondas (consulta -> resultado ->
# siguiente consulta) eso desborda el num_ctx y Ollama acaba truncando el historial
# más antiguo, perdiendo el mensaje de usuario (ollama._types.ResponseError: "no user
# query found in messages"). Se limita a los dominios que este agente realmente usa
# (work items, proyectos/equipos, sprints, repos y pipelines de lectura) para dejar
# presupuesto de contexto a la conversación real.
ADO_MCP_ALLOWED_TOOLS = [
    re.compile(r"^core_"),
    re.compile(r"^wit_"),
    re.compile(r"^work_"),
    "repo_list_repos_by_project",
    "repo_list_pull_requests_by_repo_or_project",
    "repo_get_pull_request_by_id",
    "pipelines_get_builds",
    "pipelines_list_runs",
    "pipelines_run_pipeline",
    "pipelines_get_build_status",
    "search_workitem",
]


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
        ),
        tool_filters={"allowed": ADO_MCP_ALLOWED_TOOLS},
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
        # num_ctx por defecto en Ollama es 4096 tokens. Incluso con el set de tools ya
        # recortado (ver ADO_MCP_ALLOWED_TOOLS) más el system prompt y varias rondas de
        # tool-calling (consulta -> resultado -> siguiente consulta) se necesitan bastantes
        # más tokens de los que caben por defecto. 32768 deja margen razonable sin forzar
        # tanto offload a CPU que el modelo se vuelva impracticablemente lento.
        # temperature baja: el modelo por defecto (1.0) tiende a explorar más y a
        # encadenar varios tool calls especulativos por turno, lo que agota antes el
        # contexto; con un valor más conservador es más probable que vaya paso a paso.
        model = OllamaModel(
            host="http://localhost:11434",
            model_id="qwen3.8:latest",
            options={"num_ctx": 32768},
            temperature=0.3,
        )
        agent = Agent(model=model, system_prompt=SYSTEM_INSTRUCTIONS, tools=tools)
    else:
        print("¡Ollama no está disponible! Usando sólo el core del agente Strands sin modelo local Ollama. "
              "Si ves errores de AWS/Bedrock, asegúrate de que Ollama esté activo y accesible localmente.")
        agent = Agent(system_prompt=SYSTEM_INSTRUCTIONS, tools=tools)

    print("Agente DevOps local listo. Escribe tu mensaje y pulsa Enter.")
    print("Comandos: 'salir', 'exit' o 'quit' para terminar; 'reiniciar' para vaciar el")
    print("historial de la conversación (útil si el contexto se agota); Ctrl+C también sale.\n")

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
        if user_input.lower() in {"reiniciar", "reset"}:
            agent.messages.clear()
            print("Historial de conversación vaciado.")
            continue

        try:
            # No envolver en print(): el Agent usa por defecto un PrintingCallbackHandler
            # que ya va imprimiendo (streaming) la respuesta por consola (ver doc oficial).
            agent(user_input)
        except Exception as exc:
            # Una ronda de tool-calling muy larga puede agotar el num_ctx del modelo
            # (Ollama acaba truncando el historial y el chat template falla). En vez de
            # tumbar el proceso, avisamos y dejamos seguir la conversación.
            print(f"\n[Error al generar la respuesta: {exc}]")
            print("Si el problema persiste, escribe 'reiniciar' para vaciar el historial.")

