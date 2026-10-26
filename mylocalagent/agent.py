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
        agent = Agent(model=model, system_prompt=SYSTEM_INSTRUCTIONS)
    else:
        print("¡Ollama no está disponible! Usando sólo el core del agente Strands sin modelo local Ollama. "
              "Si ves errores de AWS/Bedrock, asegúrate de que Ollama esté activo y accesible localmente.")
        agent = Agent(system_prompt=SYSTEM_INSTRUCTIONS)

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
