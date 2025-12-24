"""
Shadai Client - Base MCP Client
--------------------------------
Low-level client for communicating with Shadai MCP servers.
"""

import json
import logging
import os
from typing import Any, AsyncIterator, Dict, Optional

import aiohttp
from dotenv import load_dotenv

from .exceptions import (
    AuthenticationError,
    ConnectionError,
    ServerError,
    create_exception_from_error_response,
)

load_dotenv()

logger = logging.getLogger(__name__)


class ShadaiClient:
    """
    Async client for Shadai AI MCP servers.

    This is the low-level client that handles JSON-RPC communication
    and NDJSON streaming with automatic heartbeat handling.

    Examples:
        >>> client = ShadaiClient(api_key="your-api-key")
        >>> health = await client.health_check()
        >>> print(health)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost",
        timeout: int = 600,
    ) -> None:
        """
        Initialize Shadai client.

        Args:
            api_key: Your Shadai API key (required)
            base_url: Base URL of the Shadai server
            timeout: Request timeout in seconds

        Raises:
            ValueError: If api_key is not provided
        """
        if not api_key:
            api_key = os.getenv("SHADAI_API_KEY")
            if not api_key:
                raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        self.rpc_url = f"{self.base_url}/mcp/rpc"
        self.stream_url = f"{self.base_url}/mcp/stream"
        self.health_url = f"{self.base_url}/mcp/health"

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health and availability.

        Returns:
            Dictionary with server status, version, and available tools count

        Raises:
            ConnectionError: If server is unreachable
            ServerError: If server returns an error

        Examples:
            >>> health = await client.health_check()
            >>> print(f"Status: {health['status']}")
            >>> print(f"Tools: {health['tools']}")
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url=self.health_url) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid API key")
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to server: {e}") from e

    async def initialize(
        self,
        client_name: str = "shadai-python-client",
        client_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """
        Initialize MCP connection with server.

        Args:
            client_name: Name of your client application
            client_version: Version of your client application

        Returns:
            Server capabilities and information

        Examples:
            >>> info = await client.initialize(
            ...     client_name="my-app",
            ...     client_version="1.0.0"
            ... )
        """
        return await self.call_rpc(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": client_name,
                    "version": client_version,
                },
            },
        )

    async def list_tools(self) -> list:
        """
        List all available tools on the server.

        Returns:
            List of tool definitions with names, descriptions, and parameters

        Examples:
            >>> tools = await client.list_tools()
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        response = await self.call_rpc(method="tools/list")
        return response.get("result", {}).get("tools", [])

    async def call_rpc(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a JSON-RPC call to the server (non-streaming).

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response

        Raises:
            ServerError: If server returns an error
            ConnectionError: If connection fails
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url=self.rpc_url,
                    json=request,
                    headers=self._get_headers(),
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid API key")
                    response.raise_for_status()
                    data = await response.json()

                    # Check for JSON-RPC error format
                    if "error" in data:
                        error = data["error"]
                        raise ServerError(
                            message=f"{error.get('message', 'Unknown error')} "
                            f"(code: {error.get('code')})"
                        )

                    # Check for standardized error response format
                    result = data.get("result", {})
                    if isinstance(result, dict) and result.get("success") is False:
                        error_data = result.get("error", {})
                        exception = create_exception_from_error_response(
                            error_data=error_data
                        )
                        raise exception

                    return data
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Request failed: {e}") from e

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """
        Call a tool and get the complete response (non-streaming).

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Complete tool response as JSON string (unwrapped from standardized format)

        Raises:
            ShadaiError: If tool returns error response

        Examples:
            >>> result = await client.call_tool(
            ...     tool_name="session_create",
            ...     arguments={"name": "my-session"}
            ... )
            >>> # Returns: '{"uuid": "123", "name": "my-session", ...}'
        """
        response = await self.call_rpc(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments,
            },
        )

        content = response.get("result", {}).get("content", [])
        if not content:
            return ""

        text_response = content[0].get("text", "")
        if not text_response:
            return ""

        # Parse the response to check if it's a standardized format
        try:
            parsed = json.loads(text_response)

            # Check if it's a standardized response with success field
            if isinstance(parsed, dict) and "success" in parsed:
                if parsed.get("success") is False:
                    # Error response - create and raise exception
                    error_data = parsed.get("error", {})
                    exception = create_exception_from_error_response(
                        error_data=error_data
                    )
                    raise exception

                # Success response - unwrap and return just the data
                if parsed.get("success") is True:
                    data = parsed.get("data", {})
                    return json.dumps(data)

            # Not a standardized format - return as is
            return text_response

        except json.JSONDecodeError:
            # Not JSON - return as is
            return text_response

    async def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> AsyncIterator[str]:
        """
        Call a tool and stream response chunks (NDJSON format).

        Automatically filters out heartbeat messages.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Yields:
            Text chunks from the tool response

        Examples:
            >>> async for chunk in client.stream_tool(
            ...     tool_name="shadai_query",
            ...     arguments={"session_uuid": "...", "query": "What is ML?"}
            ... ):
            ...     print(chunk, end="", flush=True)
        """
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": 1,
        }

        timeout = aiohttp.ClientTimeout(total=None, sock_read=600)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url=self.stream_url,
                    json=request,
                    headers=self._get_headers(),
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid API key")
                    response.raise_for_status()

                    async for line in response.content:
                        line_str = line.decode("utf-8").strip()

                        if not line_str:
                            continue

                        try:
                            data = json.loads(line_str)

                            if data.get("method") == "notifications/heartbeat":
                                timestamp = data.get("params", {}).get("timestamp")
                                logger.debug(f"Heartbeat received: {timestamp}")
                                continue

                            if data.get("method") == "notifications/progress":
                                chunk = data.get("params", {}).get("progress", "")
                                if chunk:
                                    yield chunk

                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse NDJSON line: {line_str}")
                            continue

        except aiohttp.ClientError as e:
            raise ConnectionError(f"Streaming request failed: {e}") from e

    async def get_session_history(
        self,
        session_uuid: str,
        page: int = 1,
        page_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Get chat history for a session with pagination.

        Retrieves conversation messages from the checkpointer for a specific session.
        Returns messages in chronological order with pagination support.

        Args:
            session_uuid: Session UUID to retrieve history for
            page: Page number (1-indexed, default: 1)
            page_size: Messages per page (default: 5, max: 10)

        Returns:
            Dictionary containing:
            - session_uuid: The session UUID
            - session_name: The session name
            - messages: Array of message objects for current page
            - pagination: Pagination metadata

        Examples:
            >>> history = await client.get_session_history(
            ...     session_uuid="abc-123",
            ...     page=1,
            ...     page_size=5
            ... )
            >>> print(f"Page {history['pagination']['page']}/{history['pagination']['total_pages']}")
            >>> for msg in history['messages']:
            ...     print(f"[{msg['role']}]: {msg['content']}")
        """
        result = await self.call_tool(
            tool_name="session_get_history",
            arguments={
                "session_uuid": session_uuid,
                "page": page,
                "page_size": page_size,
            },
        )
        return json.loads(result)

    async def clear_session_history(
        self,
        session_uuid: str,
    ) -> Dict[str, str]:
        """
        Clear chat history for a session.

        Deletes all conversation messages from the checkpointer but keeps
        the session and uploaded files intact. Only the chat history is removed.

        Args:
            session_uuid: Session UUID to clear history for

        Returns:
            Dictionary with success message, session_uuid, and session_name

        Examples:
            >>> result = await client.clear_session_history(session_uuid="abc-123")
            >>> print(result['message'])  # "Chat history cleared successfully"
        """
        result = await self.call_tool(
            tool_name="session_clear_history",
            arguments={"session_uuid": session_uuid},
        )
        return json.loads(result)
