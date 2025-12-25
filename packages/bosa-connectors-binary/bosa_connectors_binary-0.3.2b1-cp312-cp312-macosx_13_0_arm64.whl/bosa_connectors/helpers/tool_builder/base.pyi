import abc
from abc import ABC, abstractmethod
from bosa_connectors.connector import BosaConnector as BosaConnector
from typing import Any

class BaseToolBuilder(ABC, metaclass=abc.ABCMeta):
    """Abstract base class for tool builders."""
    @abstractmethod
    def create_tool(self, service_name: str, endpoint_name: str, schema: dict, api_base_url: str, api_key: str, app_name: str, default_timeout: int) -> Any:
        """Create a tool for a given endpoint.

        Args:
            service_name (str): The name of the service.
            endpoint_name (str): The name of the endpoint.
            schema (dict): The schema definition for the endpoint.
            api_base_url (str): The base URL for the API.
            api_key (str): The API key for authentication.
            app_name (str): The name of the application.
            default_timeout (int): Default timeout in seconds for BosaConnector.

        Returns:
            The generated tool object.
        """
