"""Workflow management operations."""

import types
from typing import Any, Optional, Union, get_args, get_origin

from .store import workflow_store
from .types import WorkflowStatus


def list_workflows(status: str | None = None) -> list[dict[str, Any]]:
    """List all workflows with minimal metadata.

    Args:
        status: Optional filter by workflow status (IN_PROGRESS, COMPLETE, FAILED)

    Returns:
        List of dicts with workflow_id, status, start_time, workflow_class
    """
    store = workflow_store._read_store()

    workflows = []
    for _, workflow_data in store.items():
        workflow_info = {
            "workflow_id": workflow_data["workflow_id"],
            "status": workflow_data["status"],
            "start_time": workflow_data["start_time"],
            "workflow_class": workflow_data.get("workflow_class", "Workflow"),
        }

        # Filter by status if provided
        if status is None or workflow_info["status"] == status:
            workflows.append(workflow_info)

    return workflows


def rewind_workflow(workflow_id: str, step_id: str) -> dict[str, Any]:
    """Rewind workflow to a specific step.

    Args:
        workflow_id: The workflow to rewind
        step_id: The step to reset and replay from

    Returns:
        WorkflowStepPrompt dict with the reset step's prompt
    """
    with workflow_store.edit_workflow(workflow_id) as workflow:
        # Find the target step
        if step_id not in workflow.steps:
            raise ValueError(f"Step {step_id} not found in workflow {workflow_id}")

        step_instance = workflow.steps[step_id]

        # Reset step state
        step_instance.attempt = 1
        step_instance.current_result = None
        step_instance.status = "SUCCESS"

        # Update current step
        workflow.current_step_id = step_id

        # Update workflow status to IN_PROGRESS if it was completed/failed
        if workflow.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            workflow.status = WorkflowStatus.IN_PROGRESS

        return {
            "workflow_id": workflow.workflow_id,
            "step_id": step_instance.step_id,
            "workflow_status": workflow.status.value,
            "attempt": step_instance.attempt,
            "max_retries": step_instance.max_retries,
            "prompt": step_instance.render(),
        }


def pause_workflow(workflow_id: str) -> dict[str, Any]:
    """Pause a workflow. Can be resumed later with resume_workflow.

    Args:
        workflow_id: The workflow to pause
        reason: Optional reason for pausing

    Returns:
        Dict with workflow status info
    """
    with workflow_store.edit_workflow(workflow_id) as workflow:
        if workflow.status != WorkflowStatus.IN_PROGRESS:
            return {
                "workflow_id": workflow_id,
                "workflow_status": workflow.status.value,
                "error": f"Cannot pause workflow with status {workflow.status.value}",
            }

        workflow.status = WorkflowStatus.PAUSED

        current_step = workflow.current_step
        step_name = type(current_step).__name__ if current_step else None

        return {
            "workflow_id": workflow_id,
            "workflow_status": workflow.status.value,
            "current_step_id": workflow.current_step_id,
            "current_step_name": step_name,
            "message": (
                f"Workflow paused at step '{step_name}'. "
                "Use resume_workflow to continue."
            ),
        }


def resume_workflow(workflow_id: str) -> dict[str, Any]:
    """Resume a paused workflow by re-rendering the current step's prompt.

    Args:
        workflow_id: The workflow to resume

    Returns:
        WorkflowStepPrompt dict with the current step's prompt
    """
    with workflow_store.edit_workflow(workflow_id) as workflow:
        if workflow.status not in (WorkflowStatus.IN_PROGRESS, WorkflowStatus.PAUSED):
            return {
                "workflow_id": workflow_id,
                "workflow_status": workflow.status.value,
                "error": f"Cannot resume workflow with status {workflow.status.value}.",
            }

        if workflow.current_step_id is None or workflow.current_step is None:
            return {
                "workflow_id": workflow_id,
                "workflow_status": workflow.status.value,
                "error": "No current step to resume from.",
            }

        workflow.status = WorkflowStatus.IN_PROGRESS
        current_step = workflow.current_step

        return {
            "workflow_id": workflow_id,
            "step_id": current_step.step_id,
            "workflow_status": workflow.status.value,
            "attempt": current_step.attempt,
            "max_retries": current_step.max_retries,
            "prompt": current_step.render(resumed=True),
        }


def generate_diagram(workflow_class):
    """Create a diagram generation tool for a specific workflow.

    Args:
        workflow_class: The workflow class to create a tool for

    Returns:
        A function that generates a Mermaid diagram for the workflow
    """

    def tool() -> str:
        """Generate a Mermaid diagram for a workflow.

        Args:
            workflow_name: Name of the workflow class (default: AddFeature)

        Returns:
            Mermaid diagram as a string
        """
        # Find the start step
        if workflow_class._start_step is None:
            return f"Error: Workflow '{workflow_class.__name__}' has no start step"

        # Collect all Step subclasses by traversing from start
        step_classes = _get_step_classes(workflow_class)

        if not step_classes:
            return f"Error: Workflow '{workflow_class.__name__}' has no steps defined"

        # Build the graph by inspecting complete() return types
        edges = _build_graph(step_classes)

        # Generate Mermaid syntax
        return _generate_mermaid(workflow_class._start_step, edges)

    tool.__doc__ = f"Generate a Mermaid diagram for {workflow_class.__name__} workflow"
    return tool


def _get_step_classes(workflow_class: Any) -> dict[str, type]:
    """Get all Step subclasses by traversing the workflow graph."""
    step_classes: dict[str, type] = {}

    if not hasattr(workflow_class, "_start_step") or workflow_class._start_step is None:
        return step_classes

    # Use BFS to discover all steps starting from the start step
    to_visit: list[Any] = [workflow_class._start_step]
    visited: set[int] = set()
    step_base_class: type = workflow_class.Step

    while to_visit:
        step_class = to_visit.pop(0)

        if step_class is None or id(step_class) in visited:
            continue

        visited.add(id(step_class))
        step_classes[step_class.__name__] = step_class

        # Get the next steps from the complete() return type
        if hasattr(step_class, "complete"):
            next_step_names = _extract_next_step_names_from_method(step_class.complete)

            for step_name in next_step_names:
                next_step_class = _find_step_class(
                    step_name, step_base_class, step_classes
                )
                if next_step_class:
                    to_visit.append(next_step_class)

    return step_classes


def _find_step_class(
    step_name: str, step_base_class: type, known_steps: dict[str, type]
) -> Optional[type]:
    """Find a step class by name."""
    if step_name in known_steps:
        return known_steps[step_name]

    for subclass in step_base_class.__subclasses__():
        # Compare without workflow prefix
        subclass_simple_name = _strip_workflow_prefix(subclass.__name__)
        if subclass_simple_name == step_name:
            return subclass

    return None


def _extract_next_step_names_from_method(method) -> list[str]:
    """Extract next step names from a method's return type annotation."""
    try:
        if hasattr(method, "__annotations__"):
            return_annotation = method.__annotations__.get("return")
            if return_annotation:
                return _extract_next_steps_from_annotation(return_annotation)
    except Exception:
        pass

    return []


def _extract_next_steps_from_annotation(annotation) -> list[str]:
    """Extract step names from a type annotation."""
    next_steps = []

    if annotation is type(None) or annotation is None:
        return []

    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, types.UnionType):
        union_args = get_args(annotation)
        for arg in union_args:
            if arg is not type(None) and arg is not None:
                next_steps.extend(_extract_next_steps_from_annotation(arg))
    else:
        step_name = _extract_step_name_from_annotation(annotation)
        if step_name:
            next_steps.append(step_name)

    return next_steps


def _extract_step_name_from_annotation(annotation) -> Optional[str]:
    """Extract step class name from type["StepName"] annotation."""
    origin = get_origin(annotation)
    if origin is type:
        args = get_args(annotation)
        if args and isinstance(args[0], str):
            return _strip_workflow_prefix(args[0])

    return None


def _build_graph(
    step_classes: dict[str, type],
) -> list[tuple[str, Optional[str], Optional[str]]]:
    """Build graph edges by inspecting complete() return types."""
    edges: list[tuple[str, Optional[str], Optional[str]]] = []

    for step_name, step_class in step_classes.items():
        if not hasattr(step_class, "complete"):
            continue

        next_steps = _extract_next_step_names_from_method(step_class.complete)

        if not next_steps:
            edges.append((step_name, None, None))
        elif len(next_steps) == 1:
            edges.append((step_name, next_steps[0], None))
        else:
            for next_step in next_steps:
                edges.append((step_name, next_step, next_step))

    return edges


def _strip_workflow_prefix(step_name: str) -> str:
    """Remove workflow prefix from step name."""
    if "_" in step_name:
        parts = step_name.split("_", 1)
        if len(parts) == 2:
            return parts[1]

    return step_name


def _generate_mermaid(
    start_step: type, edges: list[tuple[str, Optional[str], Optional[str]]]
) -> str:
    """Generate Mermaid flowchart syntax from graph edges."""
    _ = start_step  # Reserved for future use
    lines = ["graph TD"]

    terminal_steps = set()

    for from_step, to_step, condition in edges:
        if to_step is None:
            terminal_steps.add(from_step)
        elif condition is None:
            from_name = _strip_workflow_prefix(from_step)
            to_name = _strip_workflow_prefix(to_step)
            lines.append(f"    {from_name}[{from_name}] --> {to_name}[{to_name}]")
        else:
            from_name = _strip_workflow_prefix(from_step)
            to_name = _strip_workflow_prefix(to_step)
            lines.append(f"    {from_name} --> {to_name}[{to_name}]")

    for terminal_step in terminal_steps:
        step_name = _strip_workflow_prefix(terminal_step)
        lines.append(f"    {step_name} --> End((End))")

    return "\n".join(lines)
