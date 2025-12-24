"""
APIVerve Toolkit for LangChain.

Provides a convenient way to get all APIVerve tools for use with LangChain agents.
Schemas are fetched from APIVerve at initialization time.
"""

import os
from typing import Any, Dict, List, Optional, Type

import requests
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from langchain_apiverve.client import APIVerveClient


# Schema source URL - always fetched fresh at init
SCHEMA_URL = "https://api.apiverve.com/publicapis/mcp-schemas.json"

# Module-level cache for schemas (persists for the lifetime of the process)
_schemas_cache: Optional[Dict] = None


def load_api_schemas(force_refresh: bool = False) -> Dict:
    """
    Load API schemas from APIVerve.

    Schemas are cached in memory after the first fetch. Subsequent calls
    return the cached schemas unless force_refresh=True.

    Args:
        force_refresh: Force re-fetch even if schemas are already cached.

    Returns:
        Dict with 'schemas' and 'totalAPIs' keys.

    Raises:
        RuntimeError: If schemas cannot be fetched from APIVerve.
    """
    global _schemas_cache

    # Return cached if available and not forcing refresh
    if _schemas_cache is not None and not force_refresh:
        return _schemas_cache

    # Fetch schemas from APIVerve (required - no fallback)
    try:
        response = requests.get(SCHEMA_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("schemas"):
            raise ValueError("Response missing 'schemas' field")

        _schemas_cache = data
        return _schemas_cache

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to fetch API schemas from {SCHEMA_URL}: {e}. "
            "APIVerve schema endpoint must be accessible to use this toolkit."
        ) from e
    except (ValueError, KeyError) as e:
        raise RuntimeError(
            f"Invalid schema response from {SCHEMA_URL}: {e}"
        ) from e


def _python_type_from_schema(param_type: str) -> Type:
    """Convert JSON schema type to Python type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return type_map.get(param_type, str)


def _create_pydantic_model(api_schema: Dict) -> Type[BaseModel]:
    """Dynamically create a Pydantic model from API schema."""
    api_id = api_schema.get("apiId", "unknown")
    parameters = api_schema.get("parameters", [])

    if not parameters:
        # No parameters - create empty model
        return create_model(f"{api_id}Input")

    # Build field definitions
    fields = {}
    for param in parameters:
        name = param.get("name", "")
        param_type = _python_type_from_schema(param.get("type", "string"))
        required = param.get("required", False)
        description = param.get("description", "")
        example = param.get("example")

        # Add example to description if available
        if example:
            description = f"{description} (e.g., {example})"

        if required:
            fields[name] = (param_type, Field(description=description))
        else:
            fields[name] = (Optional[param_type], Field(default=None, description=description))

    return create_model(f"{api_id}Input", **fields)


class DynamicAPIVerveTool(BaseTool):
    """A dynamically-created tool for a specific APIVerve API."""

    name: str = Field(description="The tool name")
    description: str = Field(description="What the tool does")
    api_id: str = Field(description="The APIVerve API identifier")
    method: str = Field(default="GET", description="HTTP method")
    client: APIVerveClient = Field(description="The API client")
    args_schema: Type[BaseModel] = Field(description="The input schema")

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute the API call."""
        # Filter out None values
        params = {k: v for k, v in kwargs.items() if v is not None}
        return self.client.call_api(self.api_id, params, method=self.method)


class APIVerveToolkit:
    """
    Toolkit for accessing APIVerve APIs through LangChain.

    Dynamically loads API schemas and creates properly-typed tools.
    Schemas are fetched from APIVerve at initialization and cached in memory.

    Example:
        >>> from langchain_apiverve import APIVerveToolkit
        >>>
        >>> # Initialize with API key
        >>> toolkit = APIVerveToolkit(api_key="your-api-key")
        >>>
        >>> # Or use environment variable APIVERVE_API_KEY
        >>> toolkit = APIVerveToolkit()
        >>>
        >>> # Get all tools (with full parameter schemas!)
        >>> tools = toolkit.get_tools()
        >>>
        >>> # Get tools for specific categories
        >>> validation_tools = toolkit.get_tools(categories=["Validation"])
        >>>
        >>> # Get only specific APIs
        >>> selected_tools = toolkit.get_tools(
        ...     include_apis=["emailvalidator", "dnslookup", "iplookup"]
        ... )

    Args:
        api_key: APIVerve API key. If not provided, uses APIVERVE_API_KEY env var.
        base_url: Base URL for API calls. Defaults to https://api.apiverve.com/v1
        refresh_schemas: Force re-fetch schemas even if already cached. Default False.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.apiverve.com/v1",
        refresh_schemas: bool = False,
    ):
        self.api_key = api_key or os.environ.get("APIVERVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide api_key parameter or set APIVERVE_API_KEY environment variable. "
                "Get your API key at https://dashboard.apiverve.com"
            )

        self.client = APIVerveClient(api_key=self.api_key, base_url=base_url)

        # Load API schemas (cached)
        schema_data = load_api_schemas(force_refresh=refresh_schemas)
        self._schemas = schema_data.get("schemas", {})
        self._total_apis = schema_data.get("totalAPIs", len(self._schemas))

    def get_tools(
        self,
        categories: Optional[List[str]] = None,
        include_apis: Optional[List[str]] = None,
        exclude_apis: Optional[List[str]] = None,
        max_tools: Optional[int] = None,
    ) -> List[BaseTool]:
        """
        Get LangChain tools for APIVerve APIs.

        Each tool has a properly-typed schema based on the API's parameters,
        so the LLM knows exactly what arguments to pass.

        Args:
            categories: Only include APIs from these categories.
            include_apis: Only include these specific API IDs.
            exclude_apis: Exclude these specific API IDs.
            max_tools: Maximum number of tools to return (for token limits).

        Returns:
            List of LangChain BaseTool instances with proper schemas.
        """
        tools: List[BaseTool] = []
        exclude_set = set(exclude_apis or [])

        for api_id, schema in self._schemas.items():
            # Skip if excluded
            if api_id in exclude_set:
                continue

            # Filter by category
            if categories and schema.get("category") not in categories:
                continue

            # Filter by include list
            if include_apis and api_id not in include_apis:
                continue

            # Create tool with dynamic schema
            try:
                tool = self._create_tool(schema)
                tools.append(tool)
            except Exception:
                # Skip APIs that fail to create (malformed schema, etc.)
                continue

            # Respect max_tools limit
            if max_tools and len(tools) >= max_tools:
                break

        return tools

    def _create_tool(self, schema: Dict) -> DynamicAPIVerveTool:
        """Create a tool from an API schema."""
        api_id = schema.get("apiId", "")
        title = schema.get("title", api_id)
        description = schema.get("description", f"Execute the {title} API")
        methods = schema.get("methods", ["GET"])
        method = methods[0] if methods else "GET"

        # Create Pydantic model from parameters
        args_schema = _create_pydantic_model(schema)

        return DynamicAPIVerveTool(
            name=api_id,
            description=description,
            api_id=api_id,
            method=method,
            client=self.client,
            args_schema=args_schema,
        )

    def get_tool(self, api_id: str) -> Optional[DynamicAPIVerveTool]:
        """
        Get a single tool by API ID.

        Args:
            api_id: The API identifier (e.g., "emailvalidator")

        Returns:
            The tool, or None if not found.
        """
        schema = self._schemas.get(api_id)
        if not schema:
            return None
        return self._create_tool(schema)

    def list_available_apis(self) -> List[Dict]:
        """
        List all available APIs.

        Returns:
            List of dicts with id, title, description, and category.
        """
        return [
            {
                "id": schema.get("apiId"),
                "title": schema.get("title"),
                "description": schema.get("description"),
                "category": schema.get("category"),
            }
            for schema in self._schemas.values()
        ]

    def list_categories(self) -> List[str]:
        """List all available API categories."""
        return sorted(set(
            schema.get("category", "Other")
            for schema in self._schemas.values()
        ))

    @property
    def total_apis(self) -> int:
        """Total number of available APIs."""
        return self._total_apis
