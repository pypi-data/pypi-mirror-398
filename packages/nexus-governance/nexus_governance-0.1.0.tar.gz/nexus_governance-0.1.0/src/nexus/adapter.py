from __future__ import annotations

import functools
import inspect
from typing import Callable

from mcp.server.fastmcp import FastMCP

from nexus.core.engine import NexusEngine
from nexus.schemas import Verdict


class NexusAdapter:
    def __init__(self, mcp_server: FastMCP, engine: NexusEngine):
        self.mcp = mcp_server
        self.engine = engine

    def tool(self, name: str, version: str = "1.0", danger: str = "read"):
        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)

            @self.mcp.tool(name=name)
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = kwargs.pop("_ctx", {}) or {}

                principal_id = ctx.get("principal_id", "unknown_user")
                principal_role = ctx.get("role", "viewer")
                scopes = ctx.get("scopes", [])
                tenant_id = ctx.get("tenant_id", "default")

                try:
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    normalized_args = dict(bound.arguments)
                except TypeError as e:
                    return {
                        "error": f"Invalid arguments: {str(e)}",
                        "valid_signature": str(sig),
                    }

                verdict, info = self.engine.evaluate(
                    tool_name=name,
                    tool_version=version,
                    args=normalized_args,
                    principal_id=principal_id,
                    principal_role=principal_role,
                    principal_scopes=scopes,
                    tenant_id=tenant_id,
                    danger=danger,
                )

                if verdict != Verdict.ALLOW:
                    return info

                req_id = (info or {}).get("request_id")
                try:
                    return await func(*args, **kwargs)
                finally:
                    if req_id:
                        self.engine.mark_executed(req_id)

            return wrapper

        return decorator
