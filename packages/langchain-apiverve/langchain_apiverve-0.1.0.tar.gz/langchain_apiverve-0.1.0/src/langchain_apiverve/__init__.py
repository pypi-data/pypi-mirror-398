"""
LangChain integration for APIVerve.

Dynamically loads 300+ utility APIs including validation, conversion,
generation, analysis, and lookup tools for AI agents.

Schemas are fetched from APIVerve at initialization and cached in memory
for the lifetime of the process.

Example:
    >>> from langchain_apiverve import APIVerveToolkit
    >>> toolkit = APIVerveToolkit(api_key="your-api-key")
    >>> tools = toolkit.get_tools()  # All 300+ tools with proper schemas!
    >>> # Use tools with any LangChain agent

For more information, see: https://docs.apiverve.com
"""

from langchain_apiverve.toolkit import APIVerveToolkit, DynamicAPIVerveTool, load_api_schemas
from langchain_apiverve.client import APIVerveClient, APIVerveError

__version__ = "0.1.0"

__all__ = [
    "APIVerveToolkit",
    "DynamicAPIVerveTool",
    "APIVerveClient",
    "APIVerveError",
    "load_api_schemas",
    "__version__",
]
