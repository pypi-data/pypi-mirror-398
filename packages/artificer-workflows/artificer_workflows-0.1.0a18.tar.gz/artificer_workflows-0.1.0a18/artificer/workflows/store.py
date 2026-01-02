import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .settings import get_workflows_dir

if TYPE_CHECKING:
    from .workflow import Workflow

logger = logging.getLogger(__name__)


def get_workflows_store_path() -> Path:
    """Get the path to the workflow executions store file."""
    workflows_dir = get_workflows_dir()
    logger.debug(f"Using workflows directory: {workflows_dir}")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return workflows_dir / "workflow_executions.json"


class WorkflowsStore:
    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path if store_path else get_workflows_store_path()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._write_store({})

    def _read_store(self) -> dict[str, Any]:
        if not self.store_path.exists():
            self._write_store({})
        with open(self.store_path, "r") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def _write_store(self, data: dict) -> None:
        with open(self.store_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_workflow(self, workflow_id: str) -> Optional["Workflow"]:
        from .workflow import Workflow

        store = self._read_store()
        data = store.get(workflow_id)
        if data is None:
            return None

        # Look up workflow class and use its serializer
        workflow_class_name = data.get("workflow_class")
        if workflow_class_name is None:
            raise ValueError("Missing workflow_class in data")

        workflow_cls = Workflow._workflow_registry.get(workflow_class_name)
        if workflow_cls is None:
            raise ValueError(f"Unknown workflow class: {workflow_class_name}")

        from .serializers import WorkflowSerializer

        serializer = getattr(workflow_cls, "serializer_class", WorkflowSerializer)()
        return serializer.from_dict(data, workflow_cls)

    def save_workflow(self, workflow: "Workflow") -> None:
        from .serializers import WorkflowSerializer

        store = self._read_store()
        serializer = getattr(type(workflow), "serializer_class", WorkflowSerializer)()
        store[workflow.workflow_id] = serializer.to_dict(workflow)
        self._write_store(store)

    @contextmanager
    def edit_workflow(self, workflow_id: str):
        """Context manager for editing and auto-saving workflows."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow_id: {workflow_id}")

        try:
            yield workflow
        finally:
            # Always save, even if exception occurred
            self.save_workflow(workflow)


workflow_store = WorkflowsStore()
