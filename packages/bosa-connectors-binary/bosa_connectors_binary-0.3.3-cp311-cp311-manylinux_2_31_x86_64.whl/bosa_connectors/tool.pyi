from .helpers.tool_builder import BaseToolBuilder as BaseToolBuilder, GllmToolBuilder as GllmToolBuilder, LangchainToolBuilder as LangchainToolBuilder
from _typeshed import Incomplete
from gllm_core.schema.tool import Tool as Tool
from langchain_core.tools import BaseTool as BaseTool
from typing import Literal, overload

class BosaConnectorToolError(Exception):
    """Base exception for BOSA connector errors."""

class BOSAConnectorToolGenerator:
    """Tool Generator for BOSA Connectors.

    This class generates tools based on OpenAPI schemas for various services.

    Attributes:
        api_base_url (str): The base URL for the API.
        api_key (str): The API key for authentication.
        info_path (str): The path to the API information endpoint.
        DEFAULT_TIMEOUT (int): Default timeout for API requests.
        app_name (str): The name of the application.

    Methods:
        generate_tools(): Generates tools for the specified services.
    """
    api_base_url: str
    api_key: str
    INFO_PATH: str
    DEFAULT_TIMEOUT: int
    app_name: str
    EXCLUDED_ENDPOINTS: Incomplete
    TOOL_BUILDER_MAP: dict[str, BaseToolBuilder]
    def __init__(self, api_base_url: str, api_key: str, app_name: str) -> None:
        """Initialize the tool generator with API base URL, info path, and app name.

        Args:
            api_base_url (str): The base URL for the API.
            api_key (str): The API key for authentication.
            app_name (str): The name of the application.
        """
    @overload
    def generate_tools(self) -> list[BaseTool]: ...
    @overload
    def generate_tools(self, tool_type: Literal['langchain']) -> list[BaseTool]: ...
    @overload
    def generate_tools(self, tool_type: Literal['gllm']) -> list[Tool]: ...
