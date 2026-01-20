"""M365 Collaboration Tool module for Amplifier.

Enables AI agent instances to collaborate across sessions via SharePoint.
"""

from typing import Any

from amplifier_core import ToolResult

from .tool import M365CollabTool, execute, get_tool_definition

# Amplifier module convention: export as 'Tool'
Tool = M365CollabTool

__all__ = ["M365CollabTool", "Tool", "execute", "get_tool_definition", "mount"]
__version__ = "0.1.0"


class M365CollabToolWrapper:
    """Amplifier tool wrapper for M365 Collaboration."""

    def __init__(self, config: dict[str, Any] | None = None):
        self._tool: M365CollabTool | None = None
        self._config = config or {}

    def _get_tool(self) -> M365CollabTool:
        """Lazy initialization of the tool instance."""
        if self._tool is None:
            self._tool = M365CollabTool()
        return self._tool

    @property
    def name(self) -> str:
        return "m365_collab"

    @property
    def description(self) -> str:
        return """Collaborate with other AI agent sessions via M365 SharePoint.

Post tasks, status updates, and handoffs that persist across sessions.
Other agents can pick up tasks you post, and you can claim tasks from others.

Operations:
- get_pending_tasks: Check for tasks from other agents
- claim_task: Claim a task (task_id)
- complete_task: Mark a task done (task_id, result?)
- post_task: Post a task for others (title, description, priority?, context?)
- post_status: Post a status update (title, status_text, task_id?)
- post_handoff: Hand off work (title, description, context)
- get_messages: Get recent messages (message_type?, status?, limit?)
- post_message: Post a general message (title, content)

Example - check for tasks:
  m365_collab(operation="get_pending_tasks")

Example - post a task:
  m365_collab(operation="post_task", title="Review auth", description="Check for security issues")"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": [
                        "post_message",
                        "post_task",
                        "post_status",
                        "post_handoff",
                        "get_messages",
                        "get_pending_tasks",
                        "claim_task",
                        "complete_task",
                    ],
                },
                "title": {"type": "string", "description": "Message/task title"},
                "content": {"type": "string", "description": "Message content"},
                "description": {"type": "string", "description": "Task description"},
                "status_text": {"type": "string", "description": "Status update text"},
                "task_id": {"type": "string", "description": "Task ID for claim/complete"},
                "priority": {"type": "string", "enum": ["high", "normal", "low"]},
                "message_type": {
                    "type": "string",
                    "enum": ["task", "status", "message", "handoff"],
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "failed"],
                },
                "context": {"type": "object", "description": "Additional context data"},
                "result": {"type": "object", "description": "Task completion result"},
                "limit": {"type": "integer", "description": "Max messages to return"},
            },
            "required": ["operation"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the m365_collab tool.

        Args:
            input_data: Tool input with operation and parameters

        Returns:
            ToolResult with operation output
        """
        operation = input_data.pop("operation", None)
        if not operation:
            return ToolResult(success=False, output={"error": "operation is required"})

        result = self._get_tool().execute(operation, **input_data)
        return ToolResult(success=result.get("success", False), output=result)


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mount the m365_collab tool into the coordinator.

    Args:
        coordinator: The Amplifier coordinator instance
        config: Optional module configuration

    Returns:
        Module metadata
    """
    tool = M365CollabToolWrapper(config)

    # Register the tool
    await coordinator.mount("tools", tool, name=tool.name)

    return {
        "name": "tool-m365-collab",
        "version": __version__,
        "provides": ["m365_collab"],
    }
