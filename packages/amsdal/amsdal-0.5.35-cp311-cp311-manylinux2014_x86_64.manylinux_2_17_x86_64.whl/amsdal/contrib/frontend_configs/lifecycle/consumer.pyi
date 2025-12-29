from _typeshed import Incomplete
from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from amsdal_utils.schemas.schema import PropertyData
from typing import Any

logger: Incomplete
core_to_frontend_types: Incomplete

def process_property(field_name: str, property_data: PropertyData) -> dict[str, Any]:
    """
    Processes a property and converts it to a frontend configuration dictionary.

    This function takes a field name and property data, and converts them into a dictionary
    that represents the configuration for a frontend form control. It handles various types
    such as core types, arrays, dictionaries, and files.

    Args:
        field_name (str): The name of the field to be processed.
        property_data (PropertyData): The property data to be processed.

    Returns:
        dict[str, Any]: A dictionary representing the frontend configuration for the given property.
    """
def populate_frontend_config_with_values(config: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """
    Populates a frontend configuration dictionary with values.

    This function takes a frontend configuration dictionary and a dictionary of values,
    and populates the configuration with the corresponding values. It recursively processes
    nested controls to ensure all values are populated.

    Args:
        config (dict[str, Any]): The frontend configuration dictionary to be populated.
        values (dict[str, Any]): The dictionary of values to populate the configuration with.

    Returns:
        dict[str, Any]: The populated frontend configuration dictionary.
    """
def get_values_from_response(response: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extracts values from a response dictionary or list of dictionaries.

    This function processes a response to extract the relevant values. It checks if the response
    is a dictionary containing a 'rows' key and processes the rows to find the appropriate values.
    If the response is not in the expected format, it returns an empty dictionary.

    Args:
        response (dict[str, Any] | list[dict[str, Any]]): The response to extract values from.

    Returns:
        dict[str, Any]: A dictionary containing the extracted values.
    """
def get_default_control(class_name: str) -> dict[str, Any]:
    """
    Retrieves the default frontend control configuration for a given class name.

    This function attempts to import a class by its name from various schema types.
    If the class is found, it converts it to a frontend configuration dictionary
    and returns it. If the class is not found, it returns an empty dictionary.

    Args:
        class_name (str): The name of the class to retrieve the default control for.

    Returns:
        dict[str, Any]: A dictionary representing the frontend control configuration for the given class.
    """

class ProcessResponseConsumer(LifecycleConsumer):
    """
    Consumer class for processing responses and populating frontend configurations.

    This class extends the LifecycleConsumer and processes responses to populate
    frontend configurations based on the class name and values extracted from the response.
    """
    def on_event(self, request: Any, response: dict[str, Any]) -> None:
        """
        Handles the event by extracting the class name and values from the request and response,
        and populates the frontend configuration accordingly.

        Args:
            request (Any): The request object containing query and path parameters.
            response (dict[str, Any]): The response dictionary to be processed.

        Returns:
            None
        """
    async def on_event_async(self, request: Any, response: dict[str, Any]) -> None:
        """
        Handles the event by extracting the class name and values from the request and response,
        and populates the frontend configuration accordingly.

        Args:
            request (Any): The request object containing query and path parameters.
            response (dict[str, Any]): The response dictionary to be processed.

        Returns:
            None
        """
