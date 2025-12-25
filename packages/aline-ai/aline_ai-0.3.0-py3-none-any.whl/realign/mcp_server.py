#!/usr/bin/env python3
"""Aline MCP Server - Query shared conversations via Model Context Protocol."""

import asyncio
import hashlib
import json
import sys
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from . import __version__

# Initialize MCP server
app = Server("aline")


def extract_share_id(share_url: str) -> str:
    """
    Extract share ID from share URL.

    Examples:
        https://realign-server.vercel.app/share/abc123 -> abc123
        https://example.com/share/xyz789/chat -> xyz789
    """
    # Remove trailing slash
    url = share_url.rstrip('/')

    # Extract path components
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]

    # Find 'share' in path and get next component
    if 'share' in path_parts:
        share_idx = path_parts.index('share')
        if share_idx + 1 < len(path_parts):
            return path_parts[share_idx + 1]

    raise ValueError(f"Could not extract share ID from URL: {share_url}")


def extract_base_url(share_url: str) -> str:
    """
    Extract base URL from share URL.

    Examples:
        https://realign-server.vercel.app/share/abc123 -> https://realign-server.vercel.app
    """
    parsed = urlparse(share_url)
    return f"{parsed.scheme}://{parsed.netloc}"


async def authenticate_share(share_url: str, password: Optional[str] = None) -> tuple[str, str, str]:
    """
    Authenticate with share and get session token.

    Args:
        share_url: The share URL
        password: Optional password for encrypted shares

    Returns:
        tuple of (base_url, share_id, session_token)

    Raises:
        ValueError: If authentication fails
        httpx.HTTPError: If network request fails
    """
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx package is required. Install with: pip install httpx")

    share_id = extract_share_id(share_url)
    base_url = extract_base_url(share_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Check if password is required
        info_resp = await client.get(f"{base_url}/api/share/{share_id}/info")
        info_resp.raise_for_status()
        info = info_resp.json()

        requires_password = info.get("requires_password", False)

        # Step 2: Authenticate
        if requires_password:
            if not password:
                raise ValueError("This share requires a password, but none was provided")

            # Hash password (SHA-256)
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            auth_resp = await client.post(
                f"{base_url}/api/share/{share_id}/auth",
                json={"password_hash": password_hash}
            )
            auth_resp.raise_for_status()
            data = auth_resp.json()
        else:
            # No password needed - create session directly
            session_resp = await client.post(
                f"{base_url}/api/share/{share_id}/session"
            )
            session_resp.raise_for_status()
            data = session_resp.json()

        session_token = data.get("session_token")
        if not session_token:
            raise ValueError("Failed to obtain session token")

        return base_url, share_id, session_token


async def ask_conversation(
    base_url: str,
    share_id: str,
    session_token: str,
    question: str
) -> str:
    """
    Send a question to the remote AI agent and receive the answer.

    Args:
        base_url: Base URL of the share service
        share_id: Share identifier
        session_token: Session token from authentication
        question: The question to ask

    Returns:
        The answer from the remote AI agent

    Raises:
        httpx.HTTPError: If network request fails
    """
    if not HTTPX_AVAILABLE:
        raise RuntimeError("httpx package is required. Install with: pip install httpx")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Send question to chat API with proper UIMessage format
        # UIMessage requires 'parts' instead of 'content'
        resp = await client.post(
            f"{base_url}/api/chat/{share_id}",
            headers={"x-session-token": session_token},
            json={"messages": [{"role": "user", "parts": [{"type": "text", "text": question}]}]}
        )
        resp.raise_for_status()

        # Parse streaming response from Vercel AI SDK
        # The AI SDK returns a UIMessageStreamResponse with multiple data chunks
        # We only need to extract the final text content
        text_chunks = []

        async for chunk in resp.aiter_text():
            # Split into lines and process each
            for line in chunk.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Remove "data: " prefix if present
                if line.startswith('data: '):
                    line = line[6:]

                # Try to parse as JSON
                try:
                    data = json.loads(line)

                    # Vercel AI SDK sends different types of chunks
                    # We're looking for text deltas (type: "text-delta")
                    if isinstance(data, dict):
                        # Extract text from text-delta chunks
                        # The field name is 'delta' not 'textDelta'
                        if data.get('type') == 'text-delta':
                            delta = data.get('delta', '')
                            if delta:
                                text_chunks.append(delta)

                except json.JSONDecodeError:
                    # Not JSON, skip
                    continue

        # Combine all text chunks to get the final answer
        answer = ''.join(text_chunks)

        # Apply reasonable length limit to prevent overwhelming the MCP client
        # If answer is too long, truncate and add notice
        MAX_RESPONSE_LENGTH = 50000  # ~50KB of text
        if len(answer) > MAX_RESPONSE_LENGTH:
            answer = answer[:MAX_RESPONSE_LENGTH] + "\n\n[Response truncated due to length. Please ask more specific questions to get complete answers.]"

        return answer if answer else "No response received from the agent."


async def handle_ask_tool(
    share_url: str,
    question: str,
    password: Optional[str] = None
) -> list[TextContent]:
    """
    Handle the ask_shared_conversation tool.

    Args:
        share_url: URL of the shared conversation
        question: Question to ask
        password: Optional password for encrypted shares

    Returns:
        List of TextContent with the answer or error
    """
    try:
        # Authenticate and get session token
        base_url, share_id, token = await authenticate_share(share_url, password)

        # Ask the question
        answer = await ask_conversation(base_url, share_id, token, question)

        # Return the answer
        return [TextContent(
            type="text",
            text=answer
        )]

    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"Authentication error: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying shared conversation: {str(e)}"
        )]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="ask_shared_conversation",
            description=(
                "Ask a question to a shared conversation. The remote AI agent will "
                "search through the conversation history and provide an answer. "
                "This enables agent-to-agent communication where your local agent "
                "can query information from a remote conversation share."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "share_url": {
                        "type": "string",
                        "description": (
                            "The full URL of the shared conversation "
                            "(e.g., https://realign-server.vercel.app/share/abc123xyz)"
                        ),
                    },
                    "question": {
                        "type": "string",
                        "description": (
                            "The question to ask about the conversation. "
                            "Be specific to get better answers from the remote agent."
                        ),
                    },
                    "password": {
                        "type": "string",
                        "description": (
                            "Password for encrypted shares (optional). "
                            "Leave empty for public shares."
                        ),
                    },
                },
                "required": ["share_url", "question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution."""
    if name == "ask_shared_conversation":
        return await handle_ask_tool(
            share_url=arguments.get("share_url", ""),
            question=arguments.get("question", ""),
            password=arguments.get("password")
        )
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def async_main():
    """Main async entry point for the MCP server."""
    # Start stdio server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the aline-mcp command."""
    # Check if httpx is available
    if not HTTPX_AVAILABLE:
        print(
            "Error: httpx package is required for aline-mcp.\n"
            "Install with: pip install httpx",
            file=sys.stderr
        )
        sys.exit(1)

    # Run the async main
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
