"""M365 Collaboration Tool - Agent-to-agent communication via SharePoint."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    import msal
    import httpx
except ImportError:
    msal = None
    httpx = None


class M365CollabTool:
    """
    Amplifier tool for M365 agent collaboration.
    
    Enables agents to communicate via SharePoint:
    - Check for tasks assigned to you
    - Respond to tasks
    - Dispatch tasks to other agents
    - Post status updates
    """

    name = "m365_collab"
    description = """Communicate with other agents via M365 SharePoint.

Operations:
- my_tasks: Get tasks assigned to you (optionally filter by status)
- respond: Respond to a task (marks it complete and posts response)
- dispatch: Send a task to another agent
- check_responses: Check for responses to your dispatched tasks
- post_status: Post a status update
- list_agents: List available agents

Examples:
  Check my pending tasks: {"operation": "my_tasks", "status": "pending"}
  Respond to a task: {"operation": "respond", "task_id": "msg-xxx", "message": "Done! Here's what I found..."}
  Ask another agent: {"operation": "dispatch", "to": "perfect-tommy", "title": "Implement cache", "instruction": "Please implement..."}
  Check responses: {"operation": "check_responses"}
"""

    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["my_tasks", "respond", "dispatch", "check_responses", "post_status", "list_agents"],
                "description": "Operation to perform"
            },
            "task_id": {
                "type": "string",
                "description": "Task ID (for respond operation)"
            },
            "message": {
                "type": "string",
                "description": "Response message or status text"
            },
            "to": {
                "type": "string",
                "description": "Target agent name (for dispatch)"
            },
            "title": {
                "type": "string",
                "description": "Task or status title"
            },
            "instruction": {
                "type": "string",
                "description": "Task instruction (for dispatch)"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "Filter by status (for my_tasks)"
            },
            "priority": {
                "type": "string",
                "enum": ["high", "normal", "low"],
                "description": "Task priority (for dispatch)"
            }
        },
        "required": ["operation"]
    }

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    FOLDER = "AgentMessages"

    # Available agents in the Banzai Institute
    AGENTS = {
        "buckaroo-banzai": {"role": "coordinator", "desc": "Leader, strategy, complex decisions"},
        "perfect-tommy": {"role": "implementer", "desc": "Building solutions, getting things done"},
        "new-jersey": {"role": "researcher", "desc": "Investigation, gathering information"},
        "reno-nevada": {"role": "reviewer", "desc": "Quality review, code review"},
        "pecos": {"role": "explorer", "desc": "Creative solutions, exploration"},
        "pinky-carruthers": {"role": "dispatcher", "desc": "Coordination, task routing"},
        "penny-priddy": {"role": "analyst", "desc": "Analysis, insights"},
        "professor-hikita": {"role": "advisor", "desc": "Wisdom, guidance"},
    }

    def __init__(self):
        self.tenant_id = os.environ.get("M365_TENANT_ID")
        self.client_id = os.environ.get("M365_CLIENT_ID")
        self.client_secret = os.environ.get("M365_CLIENT_SECRET")
        self.agent_name = os.environ.get("AGENT_NAME", "controller")
        self._app = None
        self._http = None
        self._drive_id = None

    def _ensure_clients(self):
        """Lazily initialize MSAL and HTTP clients."""
        if not msal or not httpx:
            raise RuntimeError("Required packages not installed: pip install msal httpx")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            missing = [k for k in ["M365_TENANT_ID", "M365_CLIENT_ID", "M365_CLIENT_SECRET"]
                       if not os.environ.get(k)]
            raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

        if not self._app:
            self._app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            )
        if not self._http:
            self._http = httpx.Client(timeout=30.0, follow_redirects=True)

    def _get_token(self):
        result = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Auth failed: {result.get('error_description', result)}")

    def _request(self, method, path, json_data=None, content=None):
        self._ensure_clients()
        url = f"{self.GRAPH_BASE}{path}"
        headers = {"Authorization": f"Bearer {self._get_token()}", "Content-Type": "application/json"}
        if content:
            return self._http.request(method, url, headers=headers, content=content)
        elif json_data:
            return self._http.request(method, url, headers=headers, json=json_data)
        return self._http.request(method, url, headers=headers)

    @property
    def drive_id(self):
        if not self._drive_id:
            resp = self._request("GET", "/sites/root/drive")
            if resp.status_code == 200:
                self._drive_id = resp.json()["id"]
        return self._drive_id

    def _get_messages(self, for_agent=None, from_agent=None, message_type=None, status=None, limit=50):
        resp = self._request("GET", f"/drives/{self.drive_id}/root:/{self.FOLDER}:/children?$top={limit}")
        if resp.status_code != 200:
            return []
        
        messages = []
        for item in resp.json().get("value", []):
            if not item["name"].endswith(".json"):
                continue
            url = item.get("@microsoft.graph.downloadUrl")
            if url:
                content = self._http.get(url)
                if content.status_code == 200:
                    try:
                        msg = content.json()
                        if for_agent and msg.get("to") not in [for_agent, "all"]:
                            continue
                        if from_agent and msg.get("from") != from_agent:
                            continue
                        if message_type and msg.get("message_type") != message_type:
                            continue
                        if status and msg.get("status") != status:
                            continue
                        messages.append(msg)
                    except:
                        pass
        return sorted(messages, key=lambda m: m.get("timestamp", ""), reverse=True)

    def _post_message(self, title, content, to_agent="controller", message_type="message",
                      priority="normal", in_reply_to=None):
        # Ensure folder exists
        self._request("POST", f"/drives/{self.drive_id}/root/children",
                     json_data={"name": self.FOLDER, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"})
        
        msg = {
            "id": f"msg-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": self.agent_name,
            "to": to_agent,
            "message_type": message_type,
            "title": title,
            "content": content,
            "priority": priority,
            "status": "pending" if message_type == "task" else "delivered",
        }
        if in_reply_to:
            msg["in_reply_to"] = in_reply_to
        
        resp = self._request("PUT",
                           f"/drives/{self.drive_id}/root:/{self.FOLDER}/{msg['id']}.json:/content",
                           content=json.dumps(msg, indent=2).encode())
        return msg if resp.status_code in (200, 201) else None

    def _respond_to_task(self, task_id, response_text):
        filename = f"{task_id}.json" if not task_id.endswith(".json") else task_id
        resp = self._request("GET", f"/drives/{self.drive_id}/root:/{self.FOLDER}/{filename}:/content")
        
        original_from, original_title = "controller", "Task"
        if resp.status_code == 200:
            original = resp.json()
            original_from = original.get("from", "controller")
            original_title = original.get("title", "Task")
            
            # Update original task status
            original["status"] = "completed"
            original.setdefault("context", {})["response"] = response_text
            original["context"]["responded_by"] = self.agent_name
            self._request("PUT", f"/drives/{self.drive_id}/root:/{self.FOLDER}/{filename}:/content",
                         content=json.dumps(original, indent=2).encode())
        
        # Post response message
        return self._post_message(
            title=f"Re: {original_title}",
            content=response_text,
            to_agent=original_from,
            message_type="response",
            in_reply_to=task_id,
        )

    def __call__(self, **kwargs) -> dict[str, Any]:
        """Execute the tool operation."""
        operation = kwargs.get("operation")
        
        try:
            if operation == "my_tasks":
                status = kwargs.get("status")
                tasks = self._get_messages(for_agent=self.agent_name, message_type="task", status=status)
                if not tasks:
                    return {"success": True, "message": "No tasks found", "tasks": []}
                return {
                    "success": True,
                    "count": len(tasks),
                    "tasks": [
                        {
                            "id": t["id"],
                            "from": t.get("from", "unknown"),
                            "title": t.get("title", "No title"),
                            "content": t.get("content", "")[:500],
                            "priority": t.get("priority", "normal"),
                            "status": t.get("status", "pending"),
                            "timestamp": t.get("timestamp", ""),
                        }
                        for t in tasks
                    ]
                }

            elif operation == "respond":
                task_id = kwargs.get("task_id")
                message = kwargs.get("message")
                if not task_id or not message:
                    return {"success": False, "error": "task_id and message are required"}
                
                result = self._respond_to_task(task_id, message)
                if result:
                    return {"success": True, "message": "Response posted", "response_id": result["id"]}
                return {"success": False, "error": "Failed to post response"}

            elif operation == "dispatch":
                to = kwargs.get("to")
                title = kwargs.get("title")
                instruction = kwargs.get("instruction")
                priority = kwargs.get("priority", "normal")
                
                if not all([to, title, instruction]):
                    return {"success": False, "error": "to, title, and instruction are required"}
                
                if to not in self.AGENTS and to != "all":
                    return {"success": False, "error": f"Unknown agent: {to}. Use list_agents to see available agents."}
                
                result = self._post_message(title, instruction, to_agent=to, message_type="task", priority=priority)
                if result:
                    return {"success": True, "message": f"Task dispatched to {to}", "task_id": result["id"]}
                return {"success": False, "error": "Failed to dispatch task"}

            elif operation == "check_responses":
                responses = self._get_messages(for_agent=self.agent_name, message_type="response")
                if not responses:
                    return {"success": True, "message": "No responses found", "responses": []}
                return {
                    "success": True,
                    "count": len(responses),
                    "responses": [
                        {
                            "id": r["id"],
                            "from": r.get("from", "unknown"),
                            "title": r.get("title", ""),
                            "content": r.get("content", "")[:500],
                            "in_reply_to": r.get("in_reply_to", ""),
                            "timestamp": r.get("timestamp", ""),
                        }
                        for r in responses
                    ]
                }

            elif operation == "post_status":
                title = kwargs.get("title", "Status Update")
                message = kwargs.get("message")
                if not message:
                    return {"success": False, "error": "message is required"}
                
                result = self._post_message(title, message, message_type="status")
                if result:
                    return {"success": True, "message": "Status posted", "status_id": result["id"]}
                return {"success": False, "error": "Failed to post status"}

            elif operation == "list_agents":
                return {
                    "success": True,
                    "your_identity": self.agent_name,
                    "agents": [
                        {"name": name, "role": info["role"], "description": info["desc"]}
                        for name, info in self.AGENTS.items()
                    ]
                }

            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Export for Amplifier tool loading
def create_tool():
    """Factory function for Amplifier to create the tool instance."""
    return M365CollabTool()
