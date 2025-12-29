"""Hanary API Client for MCP Server."""

import json
from typing import Optional

import requests


class HanaryClient:
    """Client for Hanary HTTP MCP API."""

    def __init__(self, api_token: str, api_url: str = "https://hanary.org"):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self._session: Optional[requests.Session] = None
        self._workspace_id_cache: dict[str, int] = {}

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "User-Agent": "curl/8.7.1",
            })
        return self._session

    async def _call_mcp(self, method: str, params: dict = None) -> dict:
        """Call the Hanary MCP endpoint."""
        session = self._get_session()

        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }

        response = session.post(f"{self.api_url}/mcp", json=request_body)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))

        return result.get("result", {})

    async def _get_workspace_id(self, workspace_slug: str) -> int:
        """Get workspace ID from slug (cached)."""
        if workspace_slug in self._workspace_id_cache:
            return self._workspace_id_cache[workspace_slug]

        result = await self._call_mcp("tools/call", {
            "name": "get_workspace",
            "arguments": {"slug": workspace_slug}
        })

        content = result.get("content", [])
        if content:
            data = json.loads(content[0].get("text", "{}"))
            workspace = data.get("workspace", {})
            workspace_id = workspace.get("id")
            if workspace_id:
                self._workspace_id_cache[workspace_slug] = workspace_id
                return workspace_id

        raise Exception(f"Workspace not found: {workspace_slug}")

    async def _call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool and return the result as string."""
        result = await self._call_mcp("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        content = result.get("content", [])
        if content:
            return content[0].get("text", "{}")
        return "{}"

    # Task methods
    async def list_tasks(
        self, workspace_slug: Optional[str] = None, include_completed: bool = False
    ) -> str:
        args = {"include_completed": include_completed}
        if workspace_slug:
            workspace_id = await self._get_workspace_id(workspace_slug)
            args["workspace_id"] = str(workspace_id)
        return await self._call_tool("list_tasks", args)

    async def create_task(
        self,
        title: str,
        workspace_slug: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        args = {"title": title}
        if workspace_slug:
            workspace_id = await self._get_workspace_id(workspace_slug)
            args["workspace_id"] = str(workspace_id)
        if description:
            args["description"] = description
        if parent_id:
            args["parent_id"] = parent_id

        return await self._call_tool("create_task", args)

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        args = {"task_id": task_id}
        if title:
            args["title"] = title
        if description:
            args["description"] = description

        return await self._call_tool("update_task", args)

    async def complete_task(self, task_id: str) -> str:
        return await self._call_tool("complete_task", {"task_id": task_id})

    async def uncomplete_task(self, task_id: str) -> str:
        return await self._call_tool("uncomplete_task", {"task_id": task_id})

    async def delete_task(self, task_id: str) -> str:
        return await self._call_tool("delete_task", {"task_id": task_id})

    async def get_top_task(self, workspace_slug: Optional[str] = None) -> str:
        args = {}
        if workspace_slug:
            workspace_id = await self._get_workspace_id(workspace_slug)
            args["workspace_id"] = str(workspace_id)
        return await self._call_tool("get_top_task", args)

    # Calibration methods (Self-Calibration feature)
    async def get_weekly_stats(self) -> str:
        return await self._call_tool("get_weekly_stats", {})

    async def get_estimation_accuracy(self) -> str:
        return await self._call_tool("get_estimation_accuracy", {})

    async def suggest_duration(self, task_id: str) -> str:
        return await self._call_tool("suggest_duration", {"task_id": task_id})

    async def detect_overload(self) -> str:
        return await self._call_tool("detect_overload", {})

    async def detect_underload(self) -> str:
        return await self._call_tool("detect_underload", {})

    # Workspace methods
    async def get_workspace(self, workspace_slug: str) -> str:
        return await self._call_tool("get_workspace", {"slug": workspace_slug})

    async def list_workspace_members(self, workspace_slug: str) -> str:
        workspace_id = await self._get_workspace_id(workspace_slug)
        return await self._call_tool("list_workspace_members", {
            "workspace_id": str(workspace_id),
        })

    # Message methods
    async def list_messages(self, workspace_slug: str, limit: int = 50) -> str:
        workspace_id = await self._get_workspace_id(workspace_slug)
        return await self._call_tool("list_messages", {
            "workspace_id": str(workspace_id),
            "limit": limit,
        })

    async def create_message(self, workspace_slug: str, content: str) -> str:
        workspace_id = await self._get_workspace_id(workspace_slug)
        return await self._call_tool("create_message", {
            "workspace_id": str(workspace_id),
            "content": content,
        })
