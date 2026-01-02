"""WorkflowModule for Artificer CLI integration."""

import os
import shlex
import sys
from typing import TYPE_CHECKING, Any

import click
import questionary
from artificer.cli.feature import ArtificerFeature
from questionary import Style
from typing_extensions import TypedDict

from .operations import list_workflows, pause_workflow, resume_workflow
from .types import WorkflowStatus
from .workflow import Workflow

if TYPE_CHECKING:
    from artificer.cli.config import ArtificerConfig


class WorkflowSelection(TypedDict):
    """Result from workflow selector."""

    workflow_name: str | None
    workflow_id: str | None
    is_resume: bool


# Custom style for questionary prompts
_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ]
)


def _format_workflow_choice(workflow: dict) -> tuple[str, str]:
    """Format a workflow for display in the selection list."""
    workflow_id = workflow["workflow_id"]
    short_id = workflow_id[:8]
    workflow_class = workflow.get("workflow_class", "Workflow")
    status = workflow["status"]

    status_indicator = {
        WorkflowStatus.IN_PROGRESS.value: "...",
        WorkflowStatus.PAUSED.value: "||",
        WorkflowStatus.COMPLETED.value: "ok",
        WorkflowStatus.FAILED.value: "x",
    }.get(status, "?")

    display = f"{workflow_class} ({short_id}) [{status_indicator}]"
    return display, workflow_id


def _select_workflow(
    status_filter: str | None = None,
    message: str = "Select a workflow:",
) -> str | None:
    """Show an interactive workflow selector."""
    workflows = list_workflows(status=status_filter)

    if not workflows:
        click.echo("No workflows found.")
        return None

    choices = []
    for wf in workflows:
        display, workflow_id = _format_workflow_choice(wf)
        choices.append(questionary.Choice(title=display, value=workflow_id))

    result: str | None = questionary.select(
        message,
        choices=choices,
        style=_style,
        use_shortcuts=False,
        use_indicator=True,
    ).ask()
    return result


def _run_workflow_selector(
    resume_only: bool = False,
) -> WorkflowSelection | None:
    """Run the workflow selection and return the selection info."""
    if resume_only:
        workflow_id = _select_workflow(message="Select a workflow to resume:")
        if workflow_id is None:
            return None

        workflows = list_workflows()
        workflow_info = next(
            (w for w in workflows if w["workflow_id"] == workflow_id), None
        )
        workflow_name = (
            workflow_info.get("workflow_class", "Workflow") if workflow_info else None
        )

        return {
            "workflow_name": workflow_name,
            "workflow_id": workflow_id,
            "is_resume": True,
        }

    # Show both new workflows and resumable ones
    available_workflows = list(Workflow._workflow_registry.keys())
    in_progress = list_workflows(status="IN_PROGRESS")
    paused = list_workflows(status="PAUSED")
    resumable = in_progress + paused

    if not available_workflows and not resumable:
        click.echo("No workflows available.")
        return None

    choices = []

    for name in available_workflows:
        choices.append(
            questionary.Choice(title=f"New: {name}", value=("new", name, None))
        )

    for wf in resumable:
        wf_name = wf.get("workflow_class", "Workflow")
        wf_id = wf["workflow_id"]
        short_id = wf_id[:8]
        status = wf["status"]
        indicator = "..." if status == "IN_PROGRESS" else "||"
        display = f"Resume: {wf_name} ({short_id}) [{indicator}]"
        choices.append(
            questionary.Choice(title=display, value=("resume", wf_name, wf_id))
        )

    result = questionary.select(
        "Select a workflow:",
        choices=choices,
        style=_style,
        use_shortcuts=False,
        use_indicator=True,
    ).ask()

    if result is None:
        return None

    action, workflow_name, workflow_id = result
    return {
        "workflow_name": workflow_name,
        "workflow_id": workflow_id,
        "is_resume": action == "resume",
    }


def _start_workflow_with_agent(workflow_name: str, agent_command: str) -> None:
    """Start a new workflow using the configured agent command."""
    prompt = f"Starting a `{workflow_name}` workflow. Start the first step."
    cmd_parts = shlex.split(agent_command)
    cmd_parts.append(prompt)
    os.execvp(cmd_parts[0], cmd_parts)


def _resume_workflow_with_agent(workflow_id: str, agent_command: str) -> None:
    """Resume a workflow using the configured agent command."""
    prompt = f"Resuming workflow `{workflow_id}`. Continue with the current step."
    cmd_parts = shlex.split(agent_command)
    cmd_parts.append(prompt)
    os.execvp(cmd_parts[0], cmd_parts)


class WorkflowsFeature(ArtificerFeature):
    """Feature providing CLI commands for workflow management."""

    @classmethod
    def register(cls, cli: click.Group, config: "ArtificerConfig") -> None:
        """Register workflow commands with the CLI."""
        workflows_config = cls._import_workflow_entrypoint(config)

        @cli.group()
        def workflows():
            """Manage workflows."""
            pass

        @workflows.command(name="list")
        def list_cmd():
            """List all workflows."""
            selected = _select_workflow(message="Workflows:")
            if selected:
                click.echo(f"Selected: {selected}")

        @workflows.command(name="start")
        @click.argument("workflow_name", required=False)
        def start_cmd(workflow_name: str | None = None):
            """Start a new workflow. Opens selector if no name given."""
            agent_command = workflows_config.get("agent_command")
            if not agent_command:
                click.echo("Error: No agent command configured.", err=True)
                click.echo("Add to pyproject.toml:", err=True)
                click.echo("  [tool.artificer.workflows]", err=True)
                click.echo('  agent_command = "claude"', err=True)
                raise SystemExit(1)

            if workflow_name is None:
                selection = _run_workflow_selector()
                if selection is None:
                    click.echo("No workflow selected.")
                    return
                workflow_name = selection["workflow_name"]
                if workflow_name is None:
                    click.echo("No workflow selected.")
                    return

            workflow_class = Workflow._workflow_registry.get(workflow_name)
            if workflow_class is None:
                available = list(Workflow._workflow_registry.keys())
                click.echo(f"Unknown workflow: {workflow_name}", err=True)
                if available:
                    click.echo(f"Available: {', '.join(available)}", err=True)
                raise SystemExit(1)

            _start_workflow_with_agent(workflow_name, agent_command)

        @workflows.command(name="resume")
        @click.argument("workflow_id", required=False)
        def resume_cmd(workflow_id: str | None = None):
            """Resume a workflow. Opens selector if no ID given."""
            agent_command = workflows_config.get("agent_command")
            if not agent_command:
                click.echo("Error: No agent command configured.", err=True)
                click.echo("Add to pyproject.toml:", err=True)
                click.echo("  [tool.artificer.workflows]", err=True)
                click.echo('  agent_command = "claude"', err=True)
                raise SystemExit(1)

            if workflow_id is None:
                selection = _run_workflow_selector(resume_only=True)
                if selection is None:
                    click.echo("No workflow selected.")
                    return
                workflow_id = selection["workflow_id"]
                if workflow_id is None:
                    click.echo("No workflow selected.")
                    return

            result = resume_workflow(workflow_id)
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
                raise SystemExit(1)

            _resume_workflow_with_agent(workflow_id, agent_command)

        @workflows.command(name="pause")
        @click.argument("workflow_id", required=False)
        def pause_cmd(workflow_id: str | None = None):
            """Pause a workflow. Opens selector if no ID given."""
            if workflow_id is None:
                selection = _run_workflow_selector(resume_only=True)
                if selection is None:
                    click.echo("No workflow selected.")
                    return
                workflow_id = selection["workflow_id"]
                if workflow_id is None:
                    click.echo("No workflow selected.")
                    return

            result = pause_workflow(workflow_id)
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
                raise SystemExit(1)
            click.echo(result.get("message", f"Paused workflow: {workflow_id}"))

    @classmethod
    def _import_workflow_entrypoint(cls, _config: "ArtificerConfig") -> dict[str, Any]:
        """Import the workflow modules to register workflows."""
        import importlib
        from pathlib import Path

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        pyproject_path = Path.cwd() / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        workflows_config: dict[str, Any] = (
            pyproject.get("tool", {}).get("artificer", {}).get("workflows", {})
        )

        # Add cwd to path so local workflow modules can be imported
        cwd = str(Path.cwd())
        sys.path.insert(0, cwd)

        workflow_modules = workflows_config.get("workflows", [])
        for module_path in workflow_modules:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                click.echo(
                    f"Warning: Could not import workflow '{module_path}': {e}",
                    err=True,
                )

        return workflows_config
