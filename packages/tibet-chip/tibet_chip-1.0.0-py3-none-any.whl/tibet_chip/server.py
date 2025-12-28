"""
TIBET Safety Chip - MCP Server

Hardware-like AI security at TPM cost.
Solves the "unsolvable" prompt injection problem.

By Claude & Jasper from HumoticaOS - Kerst 2025
"""

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .classifier import (
    classify,
    classify_web_content,
    classify_file_content,
    ContentType,
    TrustLevel,
)
from .provenance import (
    get_tracker,
    DataLocation,
    DataOperation,
)

server = Server("tibet-chip")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List TIBET Safety Chip tools."""
    return [
        Tool(
            name="safety_classify",
            description="Classify content for safety. Detects prompt injection, jailbreaks, and malicious patterns. Returns trust level and TIBET token.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to analyze"
                    },
                    "source": {
                        "type": "string",
                        "enum": ["user_input", "web_content", "file_content", "api_response", "unknown"],
                        "description": "Where this content came from",
                        "default": "unknown"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="safety_check_web",
            description="Check web content for hidden instructions or prompt injection. Use before feeding web content to an LLM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The web page content"
                    },
                    "url": {
                        "type": "string",
                        "description": "The source URL"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="track_data",
            description="Register data for provenance tracking. Creates a trail of everything that happens to this data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The data to track"
                    },
                    "source": {
                        "type": "string",
                        "description": "Where this data came from"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to group related data"
                    }
                },
                "required": ["content", "source"]
            }
        ),
        Tool(
            name="prove_handling",
            description="Prove how data was handled. Generates cryptographic proof of the data trail.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_id": {
                        "type": "string",
                        "description": "The data ID from track_data"
                    }
                },
                "required": ["data_id"]
            }
        ),
        Tool(
            name="chip_status",
            description="Get TIBET Safety Chip status and statistics.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute TIBET Safety Chip tools."""

    if name == "safety_classify":
        source_map = {
            "user_input": ContentType.USER_INPUT,
            "web_content": ContentType.WEB_CONTENT,
            "file_content": ContentType.FILE_CONTENT,
            "api_response": ContentType.API_RESPONSE,
            "unknown": ContentType.UNKNOWN,
        }
        source = source_map.get(arguments.get("source", "unknown"), ContentType.UNKNOWN)

        result = classify(arguments["content"], source)

        output = f"""TIBET Safety Chip Analysis
{'=' * 40}

Trust Level: {result.trust_level.value.upper()}
Content Type: {result.content_type.value}
Confidence: {result.confidence:.1%}
Safe to Process: {'YES' if result.safe_to_process else 'NO'}

{f'Threats Detected ({len(result.threats_detected)}):' if result.threats_detected else 'No threats detected.'}
{chr(10).join(f'  - {t}' for t in result.threats_detected) if result.threats_detected else ''}

Recommendation: {result.recommendation}

TIBET Token: {result.tibet_token['id']}
"""
        return [TextContent(type="text", text=output)]

    elif name == "safety_check_web":
        result = classify_web_content(
            arguments["content"],
            arguments.get("url", "unknown")
        )

        status = "SAFE" if result.safe_to_process else "BLOCKED"
        if result.trust_level == TrustLevel.SUSPICIOUS:
            status = "SUSPICIOUS"

        output = f"""Web Content Safety Check
{'=' * 40}

URL: {arguments.get('url', 'unknown')}
Status: {status}
Trust Level: {result.trust_level.value}

{f'Threats Found:' if result.threats_detected else 'No injection patterns detected.'}
{chr(10).join(f'  - {t}' for t in result.threats_detected) if result.threats_detected else ''}

Recommendation: {result.recommendation}

TIBET Token: {result.tibet_token['id']}
"""
        return [TextContent(type="text", text=output)]

    elif name == "track_data":
        tracker = get_tracker()
        trail = tracker.register_data(
            arguments["content"],
            arguments["source"],
            session_id=arguments.get("session_id")
        )

        output = f"""Data Registered for Tracking
{'=' * 40}

Data ID: {trail.data_id}
Content Hash: {trail.content_hash}
Location: {trail.current_location.value}
TIBET Chain Started: {trail.tibet_chain[0]}

Use 'prove_handling' with this Data ID to get the full trail.
"""
        return [TextContent(type="text", text=output)]

    elif name == "prove_handling":
        tracker = get_tracker()
        proof = tracker.prove_data_handling(arguments["data_id"])

        if "error" in proof:
            return [TextContent(type="text", text=f"Error: {proof['error']}")]

        output = f"""Data Handling Proof
{'=' * 40}

Data ID: {proof['data_id']}
Content Hash: {proof['proof']['content_hash']}
Operations: {proof['proof']['operations_count']}
Current Location: {proof['proof']['current_location']}

TIBET Chain:
{chr(10).join(f'  {i+1}. {t}' for i, t in enumerate(proof['proof']['tibet_chain']))}

Verification Hash: {proof['verification']}

This proof cryptographically demonstrates exactly what
happened to this data from entry to current state.
"""
        return [TextContent(type="text", text=output)]

    elif name == "chip_status":
        tracker = get_tracker()
        output = f"""TIBET Safety Chip Status
{'=' * 40}

Version: 1.0.0
Status: ACTIVE

Tracked Data Entries: {len(tracker.trails)}
Active Sessions: {len(tracker.active_sessions)}

Capabilities:
  - Prompt injection detection
  - Jailbreak pattern recognition
  - Data provenance tracking
  - TIBET token generation

Patterns Loaded: 20+ injection patterns

This chip provides hardware-like security for AI systems.
Like a TPM, but for language models.
"""
        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the TIBET Safety Chip MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
