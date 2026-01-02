import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Union,
    get_type_hints,
)

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from typing_extensions import TypedDict

from .operations import (
    generate_diagram,
    list_workflows,
    pause_workflow,
    resume_workflow,
    rewind_workflow,
)
from .serializers import StepSerializer, WorkflowSerializer
from .store import workflow_store
from .types import StepStatus, WorkflowStatus

if TYPE_CHECKING:
    from fastmcp import FastMCP


class Pause:
    """Sentinel class to signal that a workflow should pause.

    Return Pause(reason) from a step's complete() method to pause the workflow.
    The workflow can be resumed later with resume_workflow().

    Example:
        def complete(self, output: MyOutput) -> type["NextStep"] | Pause:
            if output.needs_user_input:
                return Pause("Waiting for user to provide additional information")
            return NextStep
    """

    def __init__(self, reason: str | None = None):
        self.reason = reason


DEFAULT_STEP_TEMPLATE = """
# Workflow: {{ workflow_name }}
## Step: {{ step_name }}

## Instructions
{{ instructions }}

## Result Schema
{{ result_schema }}

## Next Action
When complete, call `{{ workflow_name }}__complete_step` with:
  - workflow_id: {{ workflow_id }}
  - step_id: {{ step_id }}
  - status: SUCCESS or ERROR
  - output: <your output matching the schema above>

Use status=SUCCESS when the step completed successfully.
Use status=ERROR if you encountered an error - the step will be retried.
"""


class WorkflowStepPrompt(TypedDict):
    workflow_id: str
    step_id: Optional[str]
    workflow_status: str
    prompt: str
    attempt: int
    max_retries: int


def create_step_class(workflow_cls: Any) -> type:
    class Step:
        """Base class for workflow steps.
        Implement start() and complete() methods.
        """

        max_retries: int = 3
        serializer_class: type[StepSerializer] = StepSerializer

        def __init_subclass__(step_cls, start: bool = False, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            step_cls.__name__ = f"{workflow_cls.__name__}_{step_cls.__name__}"

            if not hasattr(step_cls, "start"):
                msg = f"{step_cls.__name__} must define 'start()' method"
                raise TypeError(msg)
            if not hasattr(step_cls, "complete"):
                msg = f"{step_cls.__name__} must define 'complete()' method"
                raise TypeError(msg)

            if start:
                if workflow_cls._start_step is not None:
                    msg = (
                        "Workflow already has start step: "
                        f"{workflow_cls._start_step.__name__}"
                    )
                    raise TypeError(msg)
                workflow_cls._start_step = step_cls

        def __init__(
            self,
            workflow_id: str,
            previous_result: Union[dict, None] = None,
        ):
            self.workflow_id = workflow_id
            self.step_id = self.create_step_id()
            self.attempt = 1
            self.start_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.previous_result = previous_result
            self.current_result = None
            self.status = StepStatus.SUCCESS.value
            self.prompt: Optional[str] = None

        def create_step_id(self) -> str:
            return str(uuid.uuid4())

        def render_template(self, template_name: str, *args: Any, **kwargs: Any) -> str:
            if workflow_cls._jinja_env is None:
                msg = f"Workflow '{workflow_cls.__name__}' has no templates_dir set"
                raise RuntimeError(msg)
            template = workflow_cls._jinja_env.get_template(template_name)
            return str(template.render(*args, **kwargs))

        def _get_output_schema(self) -> dict[str, Any] | None:
            """Extract the output schema from complete() type annotation.

            Returns a JSON schema dict if TypedDict is used, otherwise None.
            """
            if not hasattr(self, "complete"):
                return None
            type_hints = get_type_hints(self.complete)
            if "output" not in type_hints:
                return None
            output_type = type_hints["output"]
            # Check if it's a TypedDict
            if hasattr(output_type, "__annotations__"):
                schema: dict[str, Any] = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
                for key, val in output_type.__annotations__.items():
                    prop_type = "string"
                    if val in (int, float):
                        prop_type = "number"
                    elif val is bool:
                        prop_type = "boolean"
                    elif val is list or (
                        hasattr(val, "__origin__") and val.__origin__ is list
                    ):
                        prop_type = "array"
                    schema["properties"][key] = {"type": prop_type}
                    schema["required"].append(key)
                return schema
            return None

        def start(self, previous_result: Any = None) -> str:
            """Return the instructions for this step. Override in subclass."""
            raise NotImplementedError("Subclasses must implement start()")

        def complete(self, output: Any) -> Optional[type]:
            """Complete this step and return the next step class.

            Override in subclass.
            """
            raise NotImplementedError("Subclasses must implement complete()")

        def resume(self, _previous_result: Any) -> None:
            """Hook called before start() when resuming. Override to customize."""
            pass

        def render(self, resumed: bool = False) -> str:
            """Render the full step prompt."""
            if resumed:
                self.resume(self.previous_result)
            instructions = self.start(previous_result=self.previous_result)

            # Get result schema from complete() type annotation
            output_schema = self._get_output_schema()
            if output_schema:
                result_schema = json.dumps(output_schema, indent=2)
            else:
                result_schema = json.dumps({"type": "object"}, indent=2)

            template = Template(DEFAULT_STEP_TEMPLATE)
            rendered = template.render(
                workflow_name=workflow_cls.__name__,
                step_name=type(self).__name__,
                workflow_id=self.workflow_id,
                step_id=self.step_id,
                instructions=instructions,
                result_schema=result_schema,
            )
            self.prompt = rendered
            return rendered

    return Step


class Workflow:
    """Base class for workflows. Subclass to create a workflow."""

    _start_step: Optional[type]  # Step class to start with
    _jinja_env: Optional[Environment]  # Jinja2 environment for templates
    Step: type  # Step base class for this workflow
    templates_dir: Optional[Path] = None  # Override to set templates directory
    _shared_tools_registered: bool = False  # Track if shared tools are registered
    _workflow_registry: dict[str, type] = {}  # Map workflow class names to classes
    serializer_class: type[WorkflowSerializer] = WorkflowSerializer

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._start_step = None

        # Register workflow class for deserialization
        Workflow._workflow_registry[cls.__name__] = cls

        # Set up Jinja2 environment if templates_dir is set
        if cls.templates_dir is not None:
            cls._jinja_env = Environment(
                loader=FileSystemLoader(cls.templates_dir),
                autoescape=select_autoescape(),
            )
        else:
            cls._jinja_env = None

        cls.Step = create_step_class(cls)

    def __init__(self) -> None:
        self.workflow_id = str(uuid.uuid4())
        self.start_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.status = WorkflowStatus.IN_PROGRESS
        self.steps: dict[str, Any] = {}
        self.current_step_id: Optional[str] = None

    @property
    def current_step(self) -> Any:
        """Get the current step instance, or None if no current step."""
        if self.current_step_id is None:
            return None
        return self.steps.get(self.current_step_id)

    def get_next(
        self,
        step_instance: Any,
        output: dict[str, Any],
    ) -> Any:
        """Get the next step class by calling complete() with output."""
        return step_instance.complete(output)

    @classmethod
    def start_workflow(cls) -> WorkflowStepPrompt:
        """Start a new workflow execution and return the first step info."""
        workflow = cls()

        if cls._start_step is None:
            raise RuntimeError(f"Workflow '{cls.__name__}' has no start step defined")

        next_step = cls._start_step(workflow_id=workflow.workflow_id)
        workflow.steps[next_step.step_id] = next_step
        workflow.current_step_id = next_step.step_id
        workflow_store.save_workflow(workflow)

        return {
            "workflow_id": workflow.workflow_id,
            "step_id": next_step.step_id,
            "prompt": next_step.render(),
            "attempt": next_step.attempt,
            "max_retries": next_step.max_retries,
            "workflow_status": workflow.status.value,
        }

    @classmethod
    def complete_step(
        cls, workflow_id: str, step_id: str, status: str, output: dict[str, Any]
    ) -> WorkflowStepPrompt:
        """Complete a step and return the next step's prompt."""
        with workflow_store.edit_workflow(workflow_id) as workflow:
            current_step = workflow.steps.get(step_id)
            current_step.status = status

            # Handle ERROR status - replay the current step
            if status == "ERROR":
                step_name = type(current_step).__name__
                step_id = current_step.step_id
                attempt = current_step.attempt

                # Check if max retries exceeded
                if attempt >= current_step.max_retries:
                    workflow.status = WorkflowStatus.FAILED

                    return {
                        "workflow_id": workflow_id,
                        "step_id": step_id,
                        "workflow_status": workflow.status.value,
                        "max_retries": current_step.max_retries,
                        "attempt": attempt,
                        "prompt": (
                            f"Max retries ({current_step.max_retries}) "
                            f"exceeded for {step_name}. Workflow has failed."
                        ),
                    }

                current_step.attempt += 1
                return {
                    "workflow_id": workflow_id,
                    "step_id": current_step.step_id,
                    "workflow_status": workflow.status.value,
                    "attempt": current_step.attempt,
                    "max_retries": current_step.max_retries,
                    "prompt": current_step.render(),
                }

            current_step.current_result = output

            next_step_or_pause = workflow.get_next(current_step, output)

            # Handle Pause signal from step
            if isinstance(next_step_or_pause, Pause):
                workflow.status = WorkflowStatus.PAUSED
                step_name = type(current_step).__name__

                return {
                    "workflow_id": workflow_id,
                    "step_id": current_step.step_id,
                    "workflow_status": WorkflowStatus.PAUSED.value,
                    "attempt": current_step.attempt,
                    "max_retries": current_step.max_retries,
                    "prompt": (
                        f"Workflow paused at step '{step_name}'.\n"
                        f"Reason: {next_step_or_pause.reason or 'No reason provided'}"
                        "\n\n"
                        "Use resume_workflow to continue when ready."
                    ),
                }

            if next_step_or_pause is None:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.current_step_id = None

                return {
                    "workflow_id": workflow_id,
                    "step_id": None,
                    "workflow_status": WorkflowStatus.COMPLETED.value,
                    "attempt": 0,
                    "max_retries": 0,
                    "prompt": "Workflow complete. No further steps.",
                }

            # Instantiate the next step
            next_step = next_step_or_pause(
                workflow_id=workflow.workflow_id, previous_result=output
            )
            workflow.steps[next_step.step_id] = next_step
            workflow.current_step_id = next_step.step_id

            # Reset to IN_PROGRESS when advancing to next step
            workflow.status = WorkflowStatus.IN_PROGRESS

            return {
                "workflow_id": workflow_id,
                "step_id": next_step.step_id,
                "workflow_status": workflow.status.value,
                "attempt": next_step.attempt,
                "max_retries": next_step.max_retries,
                "prompt": next_step.render(),
            }

    @classmethod
    def register(cls, mcp: "FastMCP"):
        """Register this workflow's tools and resources with a FastMCP instance."""
        # Register shared tools once (first workflow registration only)
        if not Workflow._shared_tools_registered:
            mcp.tool()(list_workflows)
            mcp.tool()(rewind_workflow)
            mcp.tool()(pause_workflow)
            mcp.tool()(resume_workflow)
            Workflow._shared_tools_registered = True

        # Register workflow-level tools
        start_tool_name = f"{cls.__name__}__start_workflow"
        mcp.tool(name=start_tool_name)(cls.start_workflow)

        complete_tool_name = f"{cls.__name__}__complete_step"
        mcp.tool(name=complete_tool_name)(cls.complete_step)

        diagram_tool_name = f"{cls.__name__}__generate_diagram"
        mcp.tool(name=diagram_tool_name)(generate_diagram(cls))

        # Register workflow prompt
        def workflow_prompt() -> str:
            """Start a new workflow execution."""
            result = cls.start_workflow()
            return result["prompt"]

        mcp.prompt(name=cls.__name__)(workflow_prompt)
