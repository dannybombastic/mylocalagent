import asyncio
import math
import os
from datetime import date
from typing import Any

from azure_devops_mcp.azure_devops_client import AzureDevOpsClient
from strandsagents.agent import BaseAgent
from strandsagents.llm import OllamaLLM
from strandsagents.tool import Tool

from mylocalagent.system_instructions import SYSTEM_INSTRUCTIONS


DEFAULT_ORGANIZATION = "ATHINA-HADEA"
DEFAULT_PROJECT = "ATHINA LOT1"
DEFAULT_TEAM = "DevSecOps"
DEFAULT_AREA_PATH = r"ATHINA LOT1\DevSecOps"
DEFAULT_ASSIGNED_TO = "durbanod@emeal.nttdata.com"
DEFAULT_REPOSITORY = "athina-core-infrastructure"
DEFAULT_ORG_URL = f"https://dev.azure.com/{DEFAULT_ORGANIZATION}"
SPRINT_ANCHOR_NUMBER = 29
SPRINT_ANCHOR_START = date(2026, 6, 1)
SPRINT_LENGTH_DAYS = 15


def calculate_current_iteration_path(today: date | None = None) -> str:
    current_day = today or date.today()
    days_since_anchor = (current_day - SPRINT_ANCHOR_START).days
    sprint_offset = math.floor(days_since_anchor / SPRINT_LENGTH_DAYS)
    current_sprint = SPRINT_ANCHOR_NUMBER + sprint_offset
    return rf"{DEFAULT_PROJECT}\Sprint {current_sprint}"


def parse_key_value_payload(payload: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for segment in payload.split(";"):
        segment = segment.strip()
        if not segment or "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def run_async(coroutine):
    return asyncio.run(coroutine)


class AzureDevOpsTool(Tool):
    name = "azure_devops"
    description = (
        "Interact with Azure DevOps using configured defaults for ATHINA-HADEA / ATHINA LOT1. "
        "Supported commands: get_projects, get_work_item <id>, search_work_items <text>, "
        "get_work_item_types, create_task key=value;..., create_user_story key=value;..."
    )

    def __init__(self):
        super().__init__()
        self._client: AzureDevOpsClient | None = None

    def _build_client(self) -> AzureDevOpsClient:
        org_url = os.getenv("AZURE_DEVOPS_ORG_URL", DEFAULT_ORG_URL)
        project = os.getenv("AZURE_DEVOPS_PROJECT", DEFAULT_PROJECT)
        pat = os.getenv("AZURE_DEVOPS_PAT")

        if not pat:
            raise ValueError(
                "AZURE_DEVOPS_PAT no está configurado. "
                "Define la variable de entorno AZURE_DEVOPS_PAT antes de usar la tool de Azure DevOps."
            )

        auth_config = {
            "method": "pat",
            "pat": pat,
            "api_version": os.getenv("AZURE_DEVOPS_API_VERSION", "7.1"),
        }

        return AzureDevOpsClient(
            org_url=org_url,
            project=project,
            auth_config=auth_config,
        )

    @property
    def client(self) -> AzureDevOpsClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _format_work_item(self, work_item: dict[str, Any]) -> str:
        fields = work_item.get("fields", {})
        lines = [
            f"ID: {fields.get('System.Id', 'N/A')}",
            f"Type: {fields.get('System.WorkItemType', 'N/A')}",
            f"Title: {fields.get('System.Title', 'N/A')}",
            f"State: {fields.get('System.State', 'N/A')}",
            f"Assigned To: {fields.get('System.AssignedTo', 'Unassigned')}",
            f"Area Path: {fields.get('System.AreaPath', 'N/A')}",
            f"Iteration Path: {fields.get('System.IterationPath', 'N/A')}",
            f"Changed Date: {fields.get('System.ChangedDate', 'N/A')}",
        ]

        if fields.get("Microsoft.VSTS.Scheduling.StoryPoints") is not None:
            lines.append(
                f"Story Points: {fields.get('Microsoft.VSTS.Scheduling.StoryPoints')}"
            )

        if fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate") is not None:
            lines.append(
                f"Original Estimate: {fields.get('Microsoft.VSTS.Scheduling.OriginalEstimate')}"
            )
        if fields.get("Microsoft.VSTS.Scheduling.RemainingWork") is not None:
            lines.append(
                f"Remaining Work: {fields.get('Microsoft.VSTS.Scheduling.RemainingWork')}"
            )
        if fields.get("Microsoft.VSTS.Scheduling.CompletedWork") is not None:
            lines.append(
                f"Completed Work: {fields.get('Microsoft.VSTS.Scheduling.CompletedWork')}"
            )

        return "\n".join(lines)

    def _format_work_items(self, work_items: list[dict[str, Any]]) -> str:
        if not work_items:
            return "No se encontraron work items."

        formatted = []
        for item in work_items:
            fields = item.get("fields", {})
            formatted.append(
                f"- #{fields.get('System.Id', 'N/A')} "
                f"[{fields.get('System.WorkItemType', 'N/A')}] "
                f"{fields.get('System.Title', 'N/A')} | "
                f"State={fields.get('System.State', 'N/A')} | "
                f"AssignedTo={fields.get('System.AssignedTo', 'Unassigned')}"
            )
        return "\n".join(formatted)

    def _format_projects(self, projects: list[dict[str, Any]]) -> str:
        if not projects:
            return "No se encontraron proyectos."
        return "\n".join(
            f"- {project['name']} ({project['state']})" for project in projects
        )

    def _build_default_fields(
        self,
        payload: dict[str, str],
        work_item_type: str,
    ) -> dict[str, str]:
        fields: dict[str, str] = {
            "System.AreaPath": payload.get("area_path", DEFAULT_AREA_PATH),
            "System.IterationPath": payload.get(
                "iteration_path", calculate_current_iteration_path()
            ),
            "System.AssignedTo": payload.get("assigned_to", DEFAULT_ASSIGNED_TO),
        }

        if "tags" in payload:
            fields["System.Tags"] = payload["tags"]

        if work_item_type == "User Story":
            story_points = payload.get("story_points")
            if fields["System.AssignedTo"] == DEFAULT_ASSIGNED_TO and not story_points:
                raise ValueError(
                    "Para crear una User Story asignada a durbanod@emeal.nttdata.com "
                    "debes informar story_points."
                )
            if story_points:
                fields["Microsoft.VSTS.Scheduling.StoryPoints"] = story_points

        if work_item_type == "Task":
            original_estimate = payload.get("original_estimate")
            remaining_work = payload.get("remaining_work")
            completed_work = payload.get("completed_work")

            if fields["System.AssignedTo"] == DEFAULT_ASSIGNED_TO:
                missing = [
                    name
                    for name, value in {
                        "original_estimate": original_estimate,
                        "remaining_work": remaining_work,
                        "completed_work": completed_work,
                    }.items()
                    if value is None
                ]
                if missing:
                    raise ValueError(
                        "Para crear una Task asignada a durbanod@emeal.nttdata.com "
                        f"faltan campos obligatorios: {', '.join(missing)}."
                    )

            if original_estimate is not None:
                fields["Microsoft.VSTS.Scheduling.OriginalEstimate"] = original_estimate
            if remaining_work is not None:
                fields["Microsoft.VSTS.Scheduling.RemainingWork"] = remaining_work
            if completed_work is not None:
                fields["Microsoft.VSTS.Scheduling.CompletedWork"] = completed_work

        return fields

    def _create_work_item_from_payload(
        self,
        work_item_type: str,
        payload_text: str,
    ) -> str:
        payload = parse_key_value_payload(payload_text)
        title = payload.get("title")
        description = payload.get("description")

        if not title:
            raise ValueError("El campo title es obligatorio.")

        extra_fields = self._build_default_fields(payload, work_item_type)

        result = run_async(
            self.client.create_work_item(
                work_item_type=work_item_type,
                title=title,
                description=description,
                assigned_to=payload.get("assigned_to", DEFAULT_ASSIGNED_TO),
                fields=extra_fields,
                project=payload.get("project", DEFAULT_PROJECT),
            )
        )

        return "Work item creado correctamente:\n\n" + self._format_work_item(result)

    def run(self, input_text: str) -> str:
        command = input_text.strip()

        try:
            if command == "get_projects":
                projects = run_async(self.client.get_projects())
                return self._format_projects(projects)

            if command.startswith("get_work_item_types"):
                work_item_types = run_async(
                    self.client.get_work_item_types(DEFAULT_PROJECT)
                )
                return "Tipos disponibles:\n" + "\n".join(
                    f"- {item}" for item in work_item_types
                )

            if command.startswith("get_work_item "):
                work_item_id = int(command.split(maxsplit=1)[1].strip())
                work_item = run_async(self.client.get_work_item(work_item_id))
                return self._format_work_item(work_item)

            if command.startswith("search_work_items "):
                search_text = command.split(maxsplit=1)[1].strip()
                work_items = run_async(
                    self.client.search_work_items(search_text, DEFAULT_PROJECT, 20)
                )
                return self._format_work_items(work_items)

            if command.startswith("create_task "):
                payload_text = command.split(maxsplit=1)[1]
                return self._create_work_item_from_payload("Task", payload_text)

            if command.startswith("create_user_story "):
                payload_text = command.split(maxsplit=1)[1]
                return self._create_work_item_from_payload("User Story", payload_text)

            return (
                "Comando Azure DevOps no reconocido.\n\n"
                "Ejemplos soportados:\n"
                "- get_projects\n"
                "- get_work_item 12345\n"
                "- search_work_items terraform backend\n"
                "- get_work_item_types\n"
                "- create_task title=Preparar pipeline; description=Crear task inicial; "
                "original_estimate=4; remaining_work=4; completed_work=0\n"
                "- create_user_story title=Automatizar despliegue; description=Story base; story_points=5"
            )
        except Exception as exc:
            return f"Error en Azure DevOps tool: {exc}"


class OllamaAgent(BaseAgent):
    def __init__(self):
        model_name = "qwen3.8:latest"
        llm = OllamaLLM(model_name=model_name)
        super().__init__(llm=llm)

        self.add_tool(AzureDevOpsTool())
        self.system_prompt = SYSTEM_INSTRUCTIONS

    def run_agent(self, user_input: str) -> str:
        return self.chat(user_input, system_prompt=self.system_prompt)


if __name__ == "__main__":
    agent = OllamaAgent()
    print("Agente Ollama iniciado. Escribe 'exit' para salir.")

    while True:
        user_input = input("Usuario: ")
        if user_input.strip().lower() == "exit":
            break

        response = agent.run_agent(user_input)
        print("Agente:", response)
