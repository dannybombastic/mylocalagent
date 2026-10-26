# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/

from system_instructions import SYSTEM_INSTRUCTIONS
from integrations.azure_devops import AzureDevOpsConnector

from strands import Agent

if __name__ == "__main__":
    # Import dinámico sólo si Ollama realmente está instalado
    try:
        from strands.models.ollama import OllamaModel
        model = OllamaModel(host="http://localhost:11434", model_id="qwen3.8:latest")
        agent = Agent(model=model)
    except ImportError:
        # Permite ejecutar acciones alternativas si Ollama no está disponible,
        # útil para testear la integración del core/base sin servicio local
        agent = Agent()

    prompt = (
        SYSTEM_INSTRUCTIONS
        + "\n\nINSTRUCCIONES: Integra herramientas MCP y Azure DevOps según tus reglas e instrucciones."
        + "\n\nResume el propósito de este agente y explica qué capacidades base tiene para ayudar en Azure DevOps y tareas DevOps."
    )
    print(agent(prompt))
