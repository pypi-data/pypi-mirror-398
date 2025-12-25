from bosa_connectors.helpers.tool_builder.base import BaseToolBuilder as BaseToolBuilder
from bosa_connectors.helpers.tool_builder.json_schema_generator import create_input_json_schema as create_input_json_schema
from langchain_core.tools import BaseTool

class LangchainToolBuilder(BaseToolBuilder):
    """Tool builder for Langchain tools."""
    def create_tool(self, service_name: str, endpoint_name: str, schema: dict, api_base_url: str, api_key: str, app_name: str, default_timeout: int) -> BaseTool:
        """Create a Langchain tool for a given endpoint.

        Args:
            service_name (str): The name of the service.
            endpoint_name (str): The name of the endpoint.
            schema (dict): The schema definition for the endpoint.
            api_base_url (str): The base URL for the API.
            api_key (str): The API key for authentication.
            app_name (str): The name of the application.
            default_timeout (int): Default timeout in seconds for BosaConnector.

        Returns:
            BaseTool: The generated Langchain tool object.
        """
