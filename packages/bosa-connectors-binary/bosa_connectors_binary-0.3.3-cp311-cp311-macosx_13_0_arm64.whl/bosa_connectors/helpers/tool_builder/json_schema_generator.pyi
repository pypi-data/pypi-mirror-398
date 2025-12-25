from typing import Any

def create_input_json_schema(endpoint_name: str, schema: dict, default_timeout: int, service_prefix: str = 'BOSA') -> dict[str, Any]:
    '''Create a Pydantic model for the request schema.

    Args:
        endpoint_name (str): The name of the endpoint.
        schema (dict): The schema definition for the endpoint.
        default_timeout (int): Default timeout in seconds
        service_prefix (str, optional): The prefix for the service. Defaults to "BOSA".

    Returns:
        Type[BaseModel]: The generated Pydantic model.
    '''
