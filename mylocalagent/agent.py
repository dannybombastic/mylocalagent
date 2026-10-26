from system_instructions import SYSTEM_INSTRUCTIONS
from integrations.azure_devops import AzureDevOpsConnector

from strands_agents import Ollama, Agent

class MyLocalAgent(Agent):
    def __init__(self):
        self.llm = Ollama(model="qwen3.8:latest")
        self.ado = AzureDevOpsConnector()
        super().__init__(llm=self.llm)
        self.name = "MyLocalOllamaAgent"
        self.system_instructions = SYSTEM_INSTRUCTIONS

    def build_prompt(self, input_text: str) -> str:
        return f"{self.system_instructions}\n\nUsuario:\n{input_text}\n\nAsistente:"

    def run(self, input_text: str):
        prompt = self.build_prompt(input_text)
        output = self.llm.generate(prompt)
        return output


if __name__ == "__main__":
    agent = MyLocalAgent()
    prompt = (
        "Resume el propósito de este agente y explica qué capacidades base tiene "
        "para ayudar en Azure DevOps y tareas DevOps."
    )
    response = agent.run(prompt)
    print("Respuesta del agente:", response)
