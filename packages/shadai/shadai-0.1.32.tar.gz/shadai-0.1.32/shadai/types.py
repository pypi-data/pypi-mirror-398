"""
ShadAI Client Types
-------------------
Pydantic models for API responses and structured data.

These models ensure type safety and clear documentation of what
data is returned from the ShadAI API.
"""

from typing import Optional

from pydantic import BaseModel, Field


class DeepAgentJobMetadata(BaseModel):
    """
    Metadata for deep agent job execution.

    This model explicitly defines all metadata fields returned by
    deepagent tools, ensuring developers know exactly what to expect.

    Attributes:
        tool_name: Name of the deepagent tool executed (e.g., "api_designer")
        execution_time_seconds: Total execution time in seconds
        result_length: Character count of final answer
        timestamp: ISO 8601 timestamp when job completed
        model_used: LLM model identifier used for execution
        kb_documents_accessed: Number of knowledge base documents accessed (if use_knowledge_base=True)
        web_searches_performed: Number of web searches performed (if use_web_search=True)
        tokens_used: Total tokens consumed by LLM (if available from provider)
    """

    tool_name: str = Field(
        ...,
        description="Name of the deepagent tool executed",
        examples=["api_designer", "deep_report", "competitor_analyst"],
    )

    execution_time_seconds: float = Field(
        ..., description="Total execution time in seconds", ge=0.0
    )

    result_length: int = Field(..., description="Character count of final answer", ge=0)

    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when job completed",
        examples=["2025-10-22T10:30:45.123456"],
    )

    model_used: str = Field(
        ...,
        description="LLM model identifier used for execution",
        examples=["gpt-4o", "claude-sonnet-4", "gemini-2.0-flash"],
    )

    kb_documents_accessed: Optional[int] = Field(
        default=None,
        description="Number of knowledge base documents accessed (only when use_knowledge_base=True)",
        ge=0,
    )

    web_searches_performed: Optional[int] = Field(
        default=None,
        description="Number of web searches performed (only when use_web_search=True)",
        ge=0,
    )

    tokens_used: Optional[int] = Field(
        default=None,
        description="Total tokens consumed by LLM (if available from provider)",
        ge=0,
    )


class DeepAgentJobResult(BaseModel):
    """
    Standardized result structure for deep agent async jobs.

    All deepagent tools return this structure in the AsyncJob.result field.

    Attributes:
        content: The final answer/result from the agent (markdown formatted)
        metadata: Structured metadata about the execution
    """

    content: str = Field(
        ...,
        description="Final answer from the agent (markdown formatted)",
        min_length=1,
    )

    metadata: DeepAgentJobMetadata = Field(
        ..., description="Structured metadata about the execution"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "content": "# API Design Report\n\n## Executive Summary\n...",
                "metadata": {
                    "tool_name": "api_designer",
                    "execution_time_seconds": 45.3,
                    "result_length": 5420,
                    "timestamp": "2025-10-22T10:30:45.123456",
                    "model_used": "gpt-4o",
                    "kb_documents_accessed": 3,
                    "web_searches_performed": 5,
                    "tokens_used": 12450,
                },
            }
        }
