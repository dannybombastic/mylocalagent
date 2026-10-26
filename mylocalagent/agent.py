# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/

from system_instructions import SYSTEM_INSTRUCTIONS
from integrations.azure_devops import AzureDevOpsConnector

from strands import Agent
from strands.models.ollama import OllamaModel

if __name__ == "__main__":
    # Usamos explícitamente Ollama para evitar el modelo por defecto de Bedrock,
    # que requiere credenciales AWS.
    model = OllamaModel(model_id="qwen3.8:latest")
    agent = Agent(model=model)

    prompt = (
        SYSTEM_INSTRUCTIONS
        + "\n\nINSTRUCCIONES: Integra herramientas MCP y Azure DevOps según tus reglas e instrucciones."
        + "\n\nResume el propósito de este agente y explica qué capacidades base tiene para ayudar en Azure DevOps y tareas DevOps."
    )
    print(agent(prompt))
