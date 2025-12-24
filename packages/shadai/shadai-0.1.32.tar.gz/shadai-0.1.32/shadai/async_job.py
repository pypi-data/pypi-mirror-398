"""
Async Job Management for Shadai SDK
------------------------------------
Provides AsyncJob class for managing long-running background tasks.

This module implements the Handle pattern, providing a user-friendly
interface for polling and retrieving results from async deepagent jobs.

Architecture:
- Facade pattern: Simplifies complex async job operations
- Strategy pattern: Supports multiple polling strategies (wait, manual, callback)
- Single Responsibility: Only manages job lifecycle, not execution
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from .client import ShadaiClient
from .exceptions import ServerError
from .types import DeepAgentJobResult

logger = logging.getLogger(__name__)


class AsyncJob:
    """
    Handle for asynchronous deepagent job.

    Provides elegant polling and result retrieval for long-running deepagent tasks.
    Hides complexity of status polling behind a clean async interface.

    This class follows the Handle/Token pattern - it represents a reference
    to a background job and provides methods to interact with it.

    Attributes:
        id: Unique job identifier (UUID)
        client: ShadaiClient instance for MCP communication
        poll_interval: Recommended polling interval in seconds (default: 5)

    Example:
        # Elegant async pattern - polling happens behind the scenes
        async with Shadai(name="my-session") as shadai:
            job = await shadai.deep_research(topic="AI trends")

            # Wait for completion (polls automatically)
            result = await job.wait()

            # Access typed result
            print(result.content)  # Markdown formatted answer
            print(f"Tool: {result.metadata.tool_name}")
            print(f"Duration: {result.metadata.execution_time_seconds}s")
    """

    def __init__(
        self,
        job_id: str,
        client: "ShadaiClient",
        session_uuid: str,
        poll_interval: int = 5,
    ) -> None:
        """
        Initialize async job handle.

        Args:
            job_id: Unique job identifier
            client: ShadaiClient instance for API calls
            session_uuid: Session UUID for MCP tool calls
            poll_interval: Recommended polling interval in seconds
        """
        self.id = job_id
        self.client = client
        self.session_uuid = session_uuid
        self.poll_interval = poll_interval
        self._cached_status: Optional[Dict[str, Any]] = None

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current job status (lightweight polling).

        Returns status information without the full result payload.
        Efficient for repeated polling in loops.

        Returns:
            Dictionary with status information:
            {
                "job_id": "uuid",
                "status": "processing",  # pending, processing, completed, failed, cancelled
                "created_at": "2025-10-22T12:00:00Z",
                "started_at": "2025-10-22T12:00:05Z",
                "completed_at": null,
                "is_complete": false
            }

        Raises:
            ServerError: If API call fails
            ValueError: If job not found

        Example:
            status = await job.get_status()
            print(f"Status: {status['status']}")
        """
        try:
            status_str = await self.client.call_tool(
                tool_name="get_async_job_status",
                arguments={
                    "job_id": self.id,
                    "session_uuid": self.session_uuid,
                },
            )
            status = json.loads(status_str)
            self._cached_status = status
            return status
        except Exception as error:
            logger.error(f"Failed to get job status: {error}")
            raise

    async def get_result(self) -> DeepAgentJobResult:
        """
        Get typed job result (only if completed).

        Retrieves the full result payload as DeepAgentJobResult with content and metadata.
        Only works if job status is 'completed'.

        Returns:
            DeepAgentJobResult with content (markdown) and metadata (execution details)

        Raises:
            ServerError: If API call fails
            ValueError: If job not completed yet

        Example:
            # After completion
            result = await job.get_result()
            print(result.content)  # Markdown formatted answer
            print(f"Execution time: {result.metadata.execution_time_seconds}s")
        """
        try:
            result_data_str = await self.client.call_tool(
                tool_name="get_async_job_result",
                arguments={
                    "job_id": self.id,
                    "session_uuid": self.session_uuid,
                },
            )
            result_data = json.loads(result_data_str)
            # Parse result dict into Pydantic model
            return DeepAgentJobResult(**result_data["result"])
        except Exception as error:
            logger.error(f"Failed to get job result: {error}")
            raise

    async def cancel(self) -> bool:
        """
        Cancel running job.

        Stops the background task if it's still pending or processing.
        Cannot cancel jobs that are already completed, failed, or cancelled.

        Returns:
            True if successfully cancelled

        Raises:
            ServerError: If API call fails
            ValueError: If job cannot be cancelled

        Example:
            if await job.cancel():
                print("Job cancelled successfully")
        """
        try:
            response_str = await self.client.call_tool(
                tool_name="cancel_async_job",
                arguments={
                    "job_id": self.id,
                    "session_uuid": self.session_uuid,
                },
            )
            response = json.loads(response_str)
            return response["status"] == "cancelled"
        except Exception as error:
            logger.error(f"Failed to cancel job: {error}")
            raise

    @property
    async def is_complete(self) -> bool:
        """
        Check if job is in terminal state.

        Convenience property for checking if job is done (completed, failed, cancelled).
        Fetches latest status from server.

        Returns:
            True if job is in terminal state

        Example:
            if await job.is_complete:
                result = await job.get_result()
        """
        status = await self.get_status()
        return status.get("is_complete", False)

    async def wait(
        self,
        poll_interval: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> DeepAgentJobResult:
        """
        Wait for job completion and return typed result.

        Elegantly handles polling behind the scenes - just await and get your result.
        Blocks until job reaches terminal state (completed, failed, cancelled).

        This method implements the Polling pattern with configurable interval.
        Hides complexity of status checking from user code.

        Args:
            poll_interval: Seconds between status checks (default: 5)
            timeout: Optional max wait time in seconds (default: None = no timeout)

        Returns:
            DeepAgentJobResult with content and metadata if completed

        Raises:
            asyncio.TimeoutError: If timeout exceeded
            ServerError: If job failed or API error
            ValueError: If job was cancelled

        Example:
            # Elegant one-liner - polling handled automatically
            result = await job.wait()
            print(result.content)

            # With timeout for long-running jobs
            result = await job.wait(timeout=600)  # 10 minutes max
        """
        if poll_interval is None:
            poll_interval = self.poll_interval

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    raise asyncio.TimeoutError(
                        f"Job {self.id[:8]}... did not complete within {timeout}s"
                    )

            # Get status
            status = await self.get_status()

            # Check if complete
            if status["is_complete"]:
                job_status = status["status"]

                if job_status == "completed":
                    # Success - return typed result
                    return await self.get_result()
                elif job_status == "failed":
                    # Failed - raise error with job ID for debugging
                    error_msg = status.get("error_message", "Unknown error")
                    raise ServerError(f"Job {self.id[:8]}... failed: {error_msg}")
                elif job_status == "cancelled":
                    # Cancelled - raise error
                    raise ValueError(f"Job {self.id[:8]}... was cancelled")
                else:
                    # Unknown terminal state
                    raise ServerError(
                        f"Job {self.id[:8]}... in unknown terminal state: {job_status}"
                    )

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    def __repr__(self) -> str:
        """String representation of async job."""
        status_str = (
            f"status={self._cached_status['status']}"
            if self._cached_status
            else "status=unknown"
        )
        return f"AsyncJob(id={self.id[:8]}..., {status_str})"
