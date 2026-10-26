# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/

from system_instructions import SYSTEM_INSTRUCTIONS
from integrations.azure_devops import AzureDevOpsConnector

from strands import Agent

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

    if use_ollama:
        model = OllamaModel(host="http://localhost:11434", model_id="qwen3.8:latest")
        agent = Agent(model=model)
    else:
        print("¡Ollama no está disponible! Usando sólo el core del agente Strands sin modelo local Ollama. "
              "Si ves errores de AWS/Bedrock, asegúrate de que Ollama esté activo y accesible localmente.")
        agent = Agent()

    prompt = (
        SYSTEM_INSTRUCTIONS
        + "\n\nINSTRUCCIONES: Integra herramientas MCP y Azure DevOps según tus reglas e instrucciones."
        + "\n\nResume el propósito de este agente y explica qué capacidades base tiene para ayudar en Azure DevOps y tareas DevOps."
    )
    # No envolver en print(): el Agent usa por defecto un PrintingCallbackHandler
    # que ya va imprimiendo (streaming) la respuesta por consola (ver doc oficial).
    agent(prompt)
