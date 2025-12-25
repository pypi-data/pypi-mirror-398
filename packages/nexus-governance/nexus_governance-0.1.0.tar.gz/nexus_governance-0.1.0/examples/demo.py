import asyncio
import json
import logging
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from nexus.adapter import NexusAdapter
from nexus.core.engine import NexusEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo")

engine = NexusEngine(db_path="nexus.db")
mcp = FastMCP("CriticalOps")

nexus = NexusAdapter(mcp, engine)


@nexus.tool(name="deploy_firmware", danger="critical")
async def deploy_firmware(version: str, target: str) -> str:
    """
    Deploys firmware to a target server.
    This is a critical action requiring specific scopes.
    """
    logger.info("\n[SYSTEM] Starting deployment sequence...")
    logger.info(f"[SYSTEM] Payload: v{version} -> {target}")

    await asyncio.sleep(0.5)

    logger.info("[SYSTEM] ✅ Deployment verified and complete.")
    return f"Deployment of v{version} successful."


async def simulate_call(scenario_name: str, ctx: Dict[str, Any], version: str):
    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {scenario_name}")
    print(f"Actor: {ctx.get('principal_id')} | Role: {ctx.get('role')}")
    print(f"{'=' * 60}")

    try:
        result = await deploy_firmware(version, "prod-server-1", _ctx=ctx)
        print("RESULT:")

        if isinstance(result, (dict, list)):
            print(json.dumps(result, indent=2))
        else:
            print(result)

    except PermissionError as e:
        print(f"⛔ ACCESS DENIED: {e}")
    except Exception as e:
        print(f"💥 UNEXPECTED ERROR: {e}")


async def main():
    intern_ctx = {
        "principal_id": "intern",
        "role": "viewer",
        "scopes": ["read:logs"],
    }
    await simulate_call("Unauthorized Attempt", intern_ctx, "1.0.1")

    admin_ctx = {
        "principal_id": "zishan",
        "role": "admin",
        "scopes": ["critical:*", "deploy:write"],
    }
    await simulate_call("Authorized Deployment", admin_ctx, "1.0.0")


if __name__ == "__main__":
    asyncio.run(main())
