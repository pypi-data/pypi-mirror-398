"""
Shadai Client Models
--------------------
Pydantic models for type-safe tool definitions and agent configuration.
"""

import inspect
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union

from langchain_core.tools.base import create_schema_from_function
from pydantic import BaseModel, Field


class LLMModel(str, Enum):
    """Available LLM models with provider:model format."""

    # OpenAI Models
    OPENAI_GPT_5 = "openai:gpt-5"
    OPENAI_GPT_5_MINI = "openai:gpt-5-mini"
    OPENAI_GPT_5_NANO = "openai:gpt-5-nano"
    OPENAI_GPT_4_1 = "openai:gpt-4.1"
    OPENAI_GPT_4_1_MINI = "openai:gpt-4.1-mini"
    OPENAI_GPT_4O = "openai:gpt-4o"
    OPENAI_GPT_4O_MINI = "openai:gpt-4o-mini"

    # Azure Models
    AZURE_GPT_5 = "azure:gpt-5"
    AZURE_GPT_5_MINI = "azure:gpt-5-mini"
    AZURE_GPT_5_NANO = "azure:gpt-5-nano"
    AZURE_GPT_4_1 = "azure:gpt-4.1"
    AZURE_GPT_4_1_MINI = "azure:gpt-4.1-mini"
    AZURE_GPT_4O = "azure:gpt-4o"
    AZURE_GPT_4O_MINI = "azure:gpt-4o-mini"

    # Anthropic Models
    ANTHROPIC_CLAUDE_SONNET_4_5 = "anthropic:claude-sonnet-4-5-20250929"
    ANTHROPIC_CLAUDE_SONNET_4 = "anthropic:claude-sonnet-4-20250514"
    ANTHROPIC_CLAUDE_3_7_SONNET = "anthropic:claude-3-7-sonnet-latest"
    ANTHROPIC_CLAUDE_OPUS_4_1 = "anthropic:claude-opus-4-1-20250805"
    ANTHROPIC_CLAUDE_OPUS_4 = "anthropic:claude-opus-4-20250514"
    ANTHROPIC_CLAUDE_3_5_HAIKU = "anthropic:claude-3-5-haiku-latest"

    # Google Models
    GOOGLE_GEMINI_2_5_PRO = "google_genai:gemini-2.5-pro"
    GOOGLE_GEMINI_2_5_FLASH = "google_genai:gemini-2.5-flash"
    GOOGLE_GEMINI_2_5_FLASH_LITE = "google_genai:gemini-2.5-flash-lite"
    GOOGLE_GEMINI_2_0_FLASH = "google_genai:gemini-2.0-flash"
    GOOGLE_GEMINI_2_0_FLASH_LITE = "google_genai:gemini-2.0-flash-lite"

    @property
    def provider(self) -> str:
        """Extract provider from model string."""
        return self.value.split(":")[0]

    @property
    def model(self) -> str:
        """Extract model name from model string."""
        return self.value.split(":")[1]


class EmbeddingModel(str, Enum):
    """Available embedding models with provider:model format."""

    # OpenAI Embeddings
    OPENAI_TEXT_EMBEDDING_3_LARGE = "openai:text-embedding-3-large"
    OPENAI_TEXT_EMBEDDING_3_SMALL = "openai:text-embedding-3-small"

    # Azure Embeddings
    AZURE_TEXT_EMBEDDING_3_LARGE = "azure:text-embedding-3-large"
    AZURE_TEXT_EMBEDDING_3_SMALL = "azure:text-embedding-3-small"

    # Google Embeddings
    GOOGLE_GEMINI_EMBEDDING_001 = "google_genai:gemini-embedding-001"

    @property
    def provider(self) -> str:
        """Extract provider from model string."""
        return self.value.split(":")[0]

    @property
    def model(self) -> str:
        """Extract model name from model string."""
        return self.value.split(":")[1]


class LanguageCode(str, Enum):
    """Available language codes for session responses."""

    SPANISH = "es"
    ENGLISH = "en"

    @property
    def code(self) -> str:
        """Get language code."""
        return self.value


class ToolDefinition(BaseModel):
    """
    Definition of a tool for the planner.

    Attributes:
        name: Unique tool identifier
        description: Human-readable description of what the tool does
        parameters: JSON Schema defining the tool's parameters
    """

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema object defining tool parameters",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "search_database",
                "description": "Search the database for user information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        }
                    },
                    "required": ["query"],
                },
            }
        }


class Tool(BaseModel):
    """
    Complete tool specification with definition, implementation, and arguments.

    Attributes:
        definition: Tool definition for the planner
        implementation: Callable that executes the tool (can be sync or async)
        arguments: Arguments to pass to the implementation when executing
    """

    definition: ToolDefinition = Field(
        ..., description="Tool definition for the planner"
    )
    implementation: Union[Callable[..., Any], Callable[..., Any]] = Field(
        ..., description="Function that implements the tool (sync or async)"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the implementation",
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "definition": {
                    "name": "search_database",
                    "description": "Search database",
                    "parameters": {"type": "object"},
                },
                "implementation": "callable",
                "arguments": {"query": "top users", "limit": 10},
            }
        }


class AgentTool(BaseModel):
    """
    Tool definition for the Shadai Agent.

    Simple, clean interface for defining tools that the agent can use.
    The planner automatically infers arguments from the user's prompt based on
    the parameter schema you provide.

    Attributes:
        name: Unique tool identifier
        description: What the tool does
        implementation: Function that executes the tool
        arguments: Optional default arguments (planner infers from user prompt if not provided)
        parameters: JSON Schema defining tool parameters (used by planner to infer arguments)
    """

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="What the tool does")
    implementation: Union[Callable[..., Any], Callable[..., Any]] = Field(
        ..., description="Function that executes the tool (sync or async)"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional default arguments (planner infers from prompt if not provided)",
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for tool parameters (used for argument inference)",
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        implementation: Callable[..., Any],
        arguments: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "AgentTool":
        """
        Create an AgentTool instance.

        Args:
            name: Tool name
            description: Tool description
            implementation: Function that implements the tool
            arguments: Arguments to pass when executing
            parameters: Optional JSON Schema

        Returns:
            AgentTool instance
        """
        return cls(
            name=name,
            description=description,
            implementation=implementation,
            arguments=arguments or {},
            parameters=parameters,
        )

    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        parse_docstring: bool = True,
    ) -> "AgentTool":
        """
        Create an AgentTool from a function using automatic schema inference.

        Uses langchain_core's create_schema_from_function to automatically
        extract the tool name, description, and parameter schema from the
        function's signature and docstring.

        Args:
            func: Function to convert to a tool
            name: Optional override for tool name (uses func.__name__ if not provided)
            description: Optional override for description (uses docstring if not provided)
            arguments: Optional default arguments
            parse_docstring: Whether to parse Google-style docstrings for parameter descriptions

        Returns:
            AgentTool instance with auto-generated schema

        Examples:
            >>> def search_db(query: str, limit: int = 10) -> str:
            ...     '''Search the database.
            ...
            ...     Args:
            ...         query: Search query string
            ...         limit: Max results to return
            ...     '''
            ...     return "results"
            >>>
            >>> tool = AgentTool.from_function(search_db)
            >>> # Automatically extracts name, description, and parameters!
        """
        # Get function name and description
        tool_name = name or func.__name__
        tool_description = description or inspect.getdoc(func) or ""

        # Create Pydantic schema from function signature
        pydantic_schema = create_schema_from_function(
            model_name=f"{tool_name}Schema",
            func=func,
            parse_docstring=parse_docstring,
            error_on_invalid_docstring=False,
        )

        # Convert Pydantic model to JSON Schema
        json_schema = pydantic_schema.model_json_schema()

        return cls(
            name=tool_name,
            description=tool_description.strip(),
            implementation=func,
            arguments=arguments or {},
            parameters=json_schema,
        )


def tool(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    arguments: Optional[Dict[str, Any]] = None,
    parse_docstring: bool = True,
) -> Union[AgentTool, Callable[[Callable[..., Any]], AgentTool]]:
    """
    Decorator to convert a function into an AgentTool with automatic schema inference.

    Can be used with or without arguments. Automatically extracts name, description,
    and parameter schema from the function using langchain_core's utilities.

    Args:
        func: Function to convert (when used without parentheses)
        name: Optional override for tool name
        description: Optional override for description
        arguments: Optional default arguments to pass when executing
        parse_docstring: Whether to parse Google-style docstrings for parameter descriptions

    Returns:
        AgentTool instance or decorator function

    Examples:
        Basic usage (no arguments):
        >>> @tool
        ... def search_database(query: str, limit: int = 10) -> str:
        ...     '''Search the database for records.
        ...
        ...     Args:
        ...         query: Search query string
        ...         limit: Maximum number of results
        ...     '''
        ...     return "results"

        With custom name:
        >>> @tool(name="db_search")
        ... def search_database(query: str) -> str:
        ...     '''Search the database.'''
        ...     return "results"

        With default arguments:
        >>> @tool(arguments={"limit": 5})
        ... def search_database(query: str, limit: int = 10) -> str:
        ...     '''Search the database.'''
        ...     return "results"
    """

    def decorator(f: Callable[..., Any]) -> AgentTool:
        return AgentTool.from_function(
            func=f,
            name=name,
            description=description,
            arguments=arguments,
            parse_docstring=parse_docstring,
        )

    # If called without parentheses: @tool
    if func is not None:
        return decorator(func)

    # If called with parentheses: @tool() or @tool(name="...")
    return decorator


class ToolRegistry(BaseModel):
    """
    Registry of tools for the agent.

    A dictionary mapping tool names to Tool specifications.
    """

    tools: Dict[str, Tool] = Field(
        default_factory=dict, description="Dictionary of tool name to Tool"
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def add_tool(
        self,
        name: str,
        description: str,
        implementation: Callable[..., Any],
        arguments: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a tool to the registry.

        Args:
            name: Tool name
            description: Tool description
            implementation: Function that implements the tool
            arguments: Arguments to pass when executing the tool
            parameters: JSON Schema for tool parameters
        """
        self.tools[name] = Tool(
            definition=ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
            ),
            implementation=implementation,
            arguments=arguments or {},
        )

    def get_definitions(self) -> list[Dict[str, Any]]:
        """
        Get all tool definitions for the planner.

        Returns:
            List of tool definitions
        """
        return [tool.definition.model_dump() for tool in self.tools.values()]

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool or None if not found
        """
        return self.tools.get(name)
