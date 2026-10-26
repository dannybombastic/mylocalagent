import os
import requests

class AzureDevOpsConnector:
    """
    Conector minimalista para operaciones con Azure DevOps usando la API REST.
    Se puede evolucionar luego para uso con tokens, integración nativa y herramientas Strandsagents.
    """

    def __init__(self, organization=None, project=None, personal_access_token=None):
        self.organization = organization or os.environ.get("ADO_ORG", "")
        self.project = project or os.environ.get("ADO_PROJECT", "")
        self.pat = personal_access_token or os.environ.get("ADO_PAT", "")
        self.api_base = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self._session = requests.Session()
        if self.pat:
            self._session.auth = ("", self.pat)

    def get_work_items(self, wiql: str, top=5):
        """
        Consulta WIQL y devuelve work items mínimos (solo IDs y campos principales).
        """
        url = f"{self.api_base}/wit/wiql?api-version=7.1"
        payload = {"query": wiql}
        response = self._session.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("workItems", [])[:top]

    # Se podrán añadir más métodos para crear, actualizar, buscar issues y pipelines

# Ejemplo de uso mínimo (esto lo usa el agente al inicializar tools)
if __name__ == "__main__":
    # Establecer organization/project/token por variables de entorno o argumentos
    connector = AzureDevOpsConnector(
        organization="ATHINA-HADEA",
        project="ATHINA LOT1",
        personal_access_token="coloca_tu_PAT_aqui"
    )
    wiql = "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'"
    print(connector.get_work_items(wiql))
