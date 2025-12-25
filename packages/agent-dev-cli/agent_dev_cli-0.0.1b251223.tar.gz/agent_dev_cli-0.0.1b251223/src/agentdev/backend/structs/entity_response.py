from agent_framework import AgentProtocol, Workflow
from pydantic import BaseModel
from typing import Any

class EntityResponse(BaseModel):

    @classmethod
    def from_agent_framework(cls, entity: AgentProtocol | Workflow) -> "EntityResponse":
        return EntityResponse(
            id=entity.id,
            type="workflow" if isinstance(entity, Workflow) else "agent",
            name=entity.name or "",
            description=entity.description or "",
            framework="agent_framework",
            executors=list(entity.executors.keys()) if isinstance(entity, Workflow) else [],
            start_executor_id=entity.get_start_executor().id if isinstance(entity, Workflow) else None,
            workflow_dump=entity.to_dict() if isinstance(entity, Workflow) else None,
            input_schema={"type": "object"},
        )

    id: str
    type: str
    name: str
    description: str
    framework: str
    metadata: dict = {}
    executors: list[str]
    start_executor_id: str | None
    workflow_dump: dict | None = None
    input_schema: dict | None