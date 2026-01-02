"""Serializers for workflow and step persistence."""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .workflow import Workflow


class StepSerializer:
    """Base serializer for workflow steps.

    Override this class to customize step serialization for custom step attributes.
    Set `serializer_class` on your Step subclass to use a custom serializer.
    """

    def to_dict(self, step: Any) -> dict[str, Any]:
        """Serialize a step instance to dict."""
        return {
            "step_class": type(step).__name__,
            "workflow_id": step.workflow_id,
            "step_id": step.step_id,
            "attempt": step.attempt,
            "start_time": step.start_time,
            "status": step.status,
            "previous_result": self.serialize_result(step.previous_result),
            "current_result": self.serialize_result(step.current_result),
            "prompt": step.prompt,
        }

    def from_dict(self, data: dict[str, Any], step_cls: type) -> Any:
        """Deserialize a step from dict.

        Args:
            data: The serialized step data
            step_cls: The step class to instantiate

        Returns:
            A step instance with restored state
        """
        # Create step without calling __init__
        step: Any = object.__new__(step_cls)
        step.workflow_id = data["workflow_id"]
        step.step_id = data["step_id"]
        step.attempt = data["attempt"]
        step.start_time = data["start_time"]
        step.status = data["status"]
        step.previous_result = data.get("previous_result")
        step.current_result = data.get("current_result")
        step.prompt = data.get("prompt")
        return step

    def serialize_result(self, result: Any) -> Any:
        """Serialize Pydantic model or dict to JSON-compatible value."""
        if result is None:
            return None
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result


class WorkflowSerializer:
    """Base serializer for workflows.

    Override this class to customize workflow serialization for custom attributes.
    Set `serializer_class` on your Workflow subclass to use a custom serializer.
    """

    def to_dict(self, workflow: "Workflow") -> dict[str, Any]:
        """Serialize workflow to dict for JSON storage."""
        return {
            "workflow_class": type(workflow).__name__,
            "workflow_id": workflow.workflow_id,
            "start_time": workflow.start_time,
            "status": workflow.status.value,
            "current_step_id": workflow.current_step_id,
            "steps": {
                step_id: self._serialize_step(step)
                for step_id, step in workflow.steps.items()
            },
        }

    def _serialize_step(self, step: Any) -> dict[str, Any]:
        """Serialize a step using its serializer."""
        serializer = getattr(type(step), "serializer_class", StepSerializer)()
        return dict(serializer.to_dict(step))

    def from_dict(self, data: dict[str, Any], workflow_cls: type) -> "Workflow":
        """Deserialize workflow from dict.

        Args:
            data: The serialized workflow data
            workflow_cls: The workflow class to instantiate

        Returns:
            A workflow instance with restored state
        """
        from .types import WorkflowStatus

        # Create workflow without calling __init__
        workflow: "Workflow" = object.__new__(workflow_cls)
        workflow.workflow_id = data["workflow_id"]
        workflow.start_time = data["start_time"]
        workflow.status = WorkflowStatus(data["status"])
        workflow.current_step_id = data.get("current_step_id")
        workflow.steps = {}

        # Deserialize steps
        for step_id, step_data in data.get("steps", {}).items():
            step = self._deserialize_step(step_data, workflow)
            if step is not None:
                workflow.steps[step_id] = step

        return workflow

    def _deserialize_step(self, data: dict[str, Any], workflow: "Workflow") -> Any:
        """Deserialize a step from dict using its serializer."""
        step_class_name = data.get("step_class")
        if step_class_name is None:
            return None

        step_cls = self.find_step_class(step_class_name, workflow)
        if step_cls is None:
            return None

        # Use the step's serializer to deserialize
        serializer = getattr(step_cls, "serializer_class", StepSerializer)()
        return serializer.from_dict(data, step_cls)

    def find_step_class(
        self, step_class_name: str, workflow: "Workflow"
    ) -> Optional[type]:
        """Find a step class by name among this workflow's Step subclasses."""
        for subclass in type(workflow).Step.__subclasses__():
            if subclass.__name__ == step_class_name:
                return subclass
        return None
