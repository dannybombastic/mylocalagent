# Basado en la guía oficial SDK Python de strands:
# https://strandsagents.com/docs/user-guide/sdk/quickstart/python/

from system_instructions import SYSTEM_INSTRUCTIONS
from integrations.azure_devops import AzureDevOpsConnector

from strands import Agent

if __name__ == "__main__":
    # Personalización mínima inicial basada en el quickstart oficial.
    agent = Agent()
    prompt = (
        SYSTEM_INSTRUCTIONS
        + "\n\nINSTRUCCIONES: Integra herramientas MCP y Azure DevOps según tus reglas e instrucciones."
        + "\n\nResume el propósito de este agente y explica qué capacidades base tiene para ayudar en Azure DevOps y tareas DevOps."
    )
    print(agent(prompt))
