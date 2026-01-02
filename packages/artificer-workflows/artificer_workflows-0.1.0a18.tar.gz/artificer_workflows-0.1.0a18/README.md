# artificer-workflows

Build multi-step workflows that guide AI agents through complex tasks exposed as MCP tools.

> **Alpha Release** - APIs may change.

## How it works

Define workflows as Python classes with typed steps. The library registers them as tools with your FastMCP server that agents can call to execute the workflow step by step. Each step provides instructions to the agent and validates outputs using Pydantic schemas.

When an agent calls a workflow tool, it receives structured instructions for what to do. After completing the work, the agent calls back with results that are validated against the step's schema. The workflow then transitions to the next step or completes.

## Installation

```bash
pip install artificer-workflows
```

## Quick example

```python
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from artificer.workflows import Workflow

mcp = FastMCP(name="my-workflows")


class BuildFeature(Workflow):
   ...


class GatherRequirementsStep(BuildFeature.Step, start=True):
    class OutputModel(BaseModel):
        summary: str = Field(description="Summary of requirements")

    def start(self, previous_result=None) -> str:
        # return instructions
        return "Gather requirements from the user and document them."

    def complete(self, output: OutputModel) -> type["PlanStep"]:
        # returns next step
        return PlanStep


class PlanStep(BuildFeature.Step):
    class OutputModel(BaseModel):
        tasks: list[str] = Field(description="List of tasks to implement")

    def start(self, previous_result: GatherRequirementsStep.OutputModel=None) -> str:
        return f"Create an implementation plan based on: {previous_result.summary}"

    def complete(self, output: OutputModel) -> None:
        # return None to complete the workflow
        return None


BuildFeature.register(mcp)


if __name__ == "__main__":
    mcp.run()

```

Run the server and connect it to your agent. The agent can now call:
- `BuildFeature__start_workflow` - Start a new workflow
- `BuildFeature__complete_step` - Complete a step and move to the next
- `BuildFeature__generate_diagram` - Generate a Mermaid diagram of the workflow

## Features

- **Type-safe step outputs** - Pydantic schemas validate agent responses
- **Automatic MCP tool generation** - Steps become callable tools
- **Workflow state persistence** - Workflows can rewound and restarted from any step
- **Error handling and retries** - Steps can fail and retry with configurable limits
- **Template support** - Use Jinja2 templates for step instructions
- **Branching workflows** - Steps can conditionally route to different next steps
- **Mermaid Diagram** - Generate a mermaid diagram of your workflow

## License

MIT
