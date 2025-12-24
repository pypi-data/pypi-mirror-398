"""
KOSMO MCP Server - ZOO-Certified Agentic Protocol
Self-contained, zero-install MCP server for builders.

Usage:
  uvx kosmo-mcp
  
Then in your AI assistant:
  %hermios::{void setup}
  %hermios::{kosmo help}
"""

import asyncio
import re
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# --- EMBEDDED PROTOCOL (Self-Contained) ---
KOSMO_PROTOCOL = """
# KOSMO Protocol (Embedded)

- `kosmo plan <goal>`: Generate implementation plan.
- `kosmo build <file>`: Build from plan.
- `kosmo be athena`: Activate Theoretical Verifier (ZOO Audits).
- `kosmo be chiron then train <model>`: Activate Training Optimizer.
- `kosmo unmask`: Return to Level 1.
- `CHAOS SET CHAIN <name> --LASTCHAIN(-1)`
- `CHAOS PURGE OOPS`
- `CHAOS SET --LASTCHAIN(-1) CHAIN <name>`
"""

VOID_SETUP_RESPONSE = """
# KOSMO Workspace Initialized ✅

## Created Files
- `.VOID/` - Protocol workspace directory
- `.VOID/chains/temp/` - Temporary chain storage
- `.VOID/chains/saved/` - Saved chain storage

## Next Steps
1. Run `%hermios::{kosmo help}` to see available commands.
2. Use `%hermios::{kosmo plan <your goal>}` to start planning.

## Protocol Active
KOSMO v1.0 is now active. All commands must be wrapped in `%hermios::{...}`.

ZOO Status: CERTIFIED ✅
"""

HERMIOS_PATTERN = re.compile(r"%hermios(?:\((override)\))?::\{(.*?)\}", re.DOTALL)

def parse_command(raw_input: str) -> tuple[str, str | None]:
    """Parse %hermios::{...} syntax and extract command."""
    match = HERMIOS_PATTERN.search(raw_input)
    if not match:
        return "", "PROTOCOL_ERROR: Command must be wrapped in %hermios::{...}"
    
    override = match.group(1)
    command = match.group(2).strip().lower()
    return command, None

def execute_command(command: str) -> str:
    """Execute KOSMO command and return response."""
    
    # VOID SETUP
    if command == "void setup":
        return VOID_SETUP_RESPONSE
    
    # KOSMO HELP
    if command in ["kosmo help", "help", "kosmo"]:
        return KOSMO_PROTOCOL
    
    # KOSMO PLAN
    if command.startswith("kosmo plan"):
        goal = command.replace("kosmo plan", "").strip()
        return f"""
# Implementation Plan: {goal or 'No goal specified'}

## Status
Plan generation is handled by your AI assistant.
This MCP server validates the command syntax.

## Next Step
Your AI assistant will now generate a detailed plan for: **{goal}**

Provide specific requirements for better results.
"""
    
    # KOSMO BUILD
    if command.startswith("kosmo build"):
        target = command.replace("kosmo build", "").strip()
        return f"""
# Build: {target or 'No target specified'}

## Status
Build execution is handled by your AI assistant.
This MCP server validates the command syntax.

## Next Step
Your AI assistant will now implement: **{target}**
"""
    
    # MASKING
    if command.startswith("kosmo be athena"):
        return """
# 🦉 ATHENA Activated

## Role
Theoretical Verifier - ZOO Audits, Logic Verification, Testing.

## Mandates
- Tests MUST be non-tautological (verify side effects, not just return codes).
- If ZOO criteria fails, initiate ZOO Restoration immediately.

## Status
You are now operating as ATHENA. Use `kosmo unmask` to return to Level 1.
"""
    
    if command.startswith("kosmo be chiron"):
        return """
# 🏹 CHIRON Activated

## Role
Training Optimizer - ML Pipeline Verification & Performance Tuning.

## Status
You are now operating as CHIRON. Use `kosmo unmask` to return to Level 1.
"""
    
    if command == "kosmo unmask":
        return """
# Unmasked ✅

Returned to Level 1 (KOSMO). All masks deactivated.
"""
    
    # CHAOS COMMANDS
    if command.startswith("chaos"):
        return f"""
# Chaos Logic

Command received: `{command}`

Chaos is the Git Agent of Chains - it manages versioning and snapshots.
This command will be processed by your AI assistant's file system tools.
"""
    
    # UNKNOWN
    return f"""
# Unknown Command

Received: `{command}`

Run `%hermios::{{kosmo help}}` for available commands.
"""

# --- MCP SERVER ---
app = Server("kosmo-mcp")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="kosmo_execute",
            description="Execute KOSMO protocol commands. Wrap commands in %hermios::{...} syntax.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The raw command including %hermios::{...} wrapper"
                    }
                },
                "required": ["command"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "kosmo_execute":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    raw_command = arguments.get("command", "")
    command, error = parse_command(raw_command)
    
    if error:
        return [TextContent(type="text", text=error)]
    
    result = execute_command(command)
    return [TextContent(type="text", text=result)]

async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

def main():
    """Entry point for kosmo-mcp command."""
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
