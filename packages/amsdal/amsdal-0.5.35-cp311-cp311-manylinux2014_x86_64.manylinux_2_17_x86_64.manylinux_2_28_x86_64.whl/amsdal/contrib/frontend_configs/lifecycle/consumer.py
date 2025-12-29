# mypy: disable-error-code="arg-type"
import contextlib
import logging
from typing import Any

from amsdal_models.classes.errors import AmsdalClassNotFoundError
from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.data_models.core import LegacyDictSchema
from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.models.enums import Versions
from amsdal_utils.schemas.schema import PropertyData

logger = logging.getLogger(__name__)

core_to_frontend_types = {
    CoreTypes.NUMBER.value: 'number',
    CoreTypes.INTEGER.value: 'integer',
    CoreTypes.BOOLEAN.value: 'checkbox',
    CoreTypes.STRING.value: 'text',
    CoreTypes.ANYTHING.value: 'text',
    CoreTypes.BINARY.value: 'text',
    CoreTypes.DATE.value: 'date',
    CoreTypes.DATETIME.value: 'datetime',
}


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
    type_definition: dict[str, Any]
    if property_data.type in core_to_frontend_types:
        type_definition = {
            'type': core_to_frontend_types[property_data.type],
        }
    elif property_data.type == CoreTypes.ARRAY.value:
        type_definition = {
            'type': 'array',
            'control': process_property(f'{field_name}_items', property_data.items),  # type: ignore[arg-type]
        }
    elif property_data.type == CoreTypes.DICTIONARY.value:
        if isinstance(property_data.items, LegacyDictSchema):
            type_definition = {
                'type': 'dict',
                'control': process_property(
                    f'{field_name}_items',
                    PropertyData(
                        type=property_data.items.key_type,
                        items=None,
                        title=None,
                        read_only=False,
                        options=None,
                        default=None,
                        field_name=field_name,
                        field_id=None,
                        is_deleted=False,
                    ),
                ),
            }
        else:
            type_definition = {
                'type': 'dict',
                'control': process_property(
                    f'{field_name}_items',
                    property_data.items.key,  # type: ignore[union-attr, arg-type]
                ),
            }
    elif property_data.type == 'File':
        type_definition = {
            'type': 'file',
        }
    else:
        type_definition = {
            'type': 'object_latest',
            'entityType': property_data.type,
        }

    if getattr(property_data, 'default', None) is not None:
        type_definition['value'] = property_data.default

    if getattr(property_data, 'options', None) is not None:
        type_definition['options'] = [
            {
                'label': option.key,
                'value': option.value,
            }
            for option in property_data.options  # type: ignore[union-attr]
        ]

    return {
        'name': field_name,
        'label': property_data.title if hasattr(property_data, 'title') and property_data.title else field_name,
        **type_definition,
    }


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
    if config.get('controls') and isinstance(config['controls'], list):
        for control in config['controls']:
            populate_frontend_config_with_values(control, values)

    if config.get('name') in values:
        config['value'] = values[config['name']]

    return config


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
    if not isinstance(response, dict) or 'rows' not in response or not response['rows']:
        return {}

    for row in response['rows']:
        if '_metadata' in row and row['_metadata'].get('next_version') is None:
            return row

    return response['rows'][0]


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
    from amsdal_models.classes.class_manager import ClassManager

    from amsdal.contrib.frontend_configs.conversion import convert_to_frontend_config
    from amsdal.contrib.frontend_configs.models.frontend_control_config import (
        FrontendControlConfig,  # type: ignore[import-not-found]
    )
    from amsdal.models.core.file import File

    target_class = None
    with contextlib.suppress(AmsdalClassNotFoundError):
        target_class = ClassManager().import_class(class_name)

    if not target_class:
        return {}

    if target_class is File:
        config = {
            'type': 'group',
            'name': 'File',
            'label': 'File',
            'controls': [
                {'label': 'Filename', 'name': 'filename', 'type': 'text', 'required': True},
                {'label': 'Data', 'name': 'data', 'type': 'Bytes', 'required': True},
                {'label': 'Size', 'name': 'size', 'type': 'number', 'required': False},
            ],
        }
    else:
        config = convert_to_frontend_config(target_class, is_transaction=False)

    return FrontendControlConfig(**config).model_dump(
        exclude_none=True,
    )


class ProcessResponseConsumer(LifecycleConsumer):
    """
    Consumer class for processing responses and populating frontend configurations.

    This class extends the LifecycleConsumer and processes responses to populate
    frontend configurations based on the class name and values extracted from the response.
    """

    def on_event(
        self,
        request: Any,
        response: dict[str, Any],
    ) -> None:
        """
        Handles the event by extracting the class name and values from the request and response,
        and populates the frontend configuration accordingly.

        Args:
            request (Any): The request object containing query and path parameters.
            response (dict[str, Any]): The response dictionary to be processed.

        Returns:
            None
        """
        from amsdal.contrib.frontend_configs.models.frontend_model_config import (
            FrontendModelConfig,  # type: ignore[import-not-found]
        )

        class_name = None
        values = {}
        if hasattr(request, 'query_params') and 'class_name' in request.query_params:
            class_name = request.query_params['class_name']

        if hasattr(request, 'path_params') and 'address' in request.path_params:
            class_name = Address.from_string(request.path_params['address']).class_name
            values = get_values_from_response(response)

        if class_name and isinstance(response, dict):
            config = (
                FrontendModelConfig.objects.all()
                .first(
                    class_name=class_name,
                    _metadata__is_deleted=False,
                    _address__object_version=Versions.LATEST,
                )
                .execute()
            )

            if config and config.control:
                response['control'] = populate_frontend_config_with_values(
                    config.control.model_dump(exclude_none=True), values
                )
            else:
                response['control'] = populate_frontend_config_with_values(get_default_control(class_name), values)

    async def on_event_async(
        self,
        request: Any,
        response: dict[str, Any],
    ) -> None:
        """
        Handles the event by extracting the class name and values from the request and response,
        and populates the frontend configuration accordingly.

        Args:
            request (Any): The request object containing query and path parameters.
            response (dict[str, Any]): The response dictionary to be processed.

        Returns:
            None
        """
        from amsdal.contrib.frontend_configs.models.frontend_model_config import (
            FrontendModelConfig,  # type: ignore[import-not-found]
        )

        class_name = None
        values = {}
        if hasattr(request, 'query_params') and 'class_name' in request.query_params:
            class_name = request.query_params['class_name']

        if hasattr(request, 'path_params') and 'address' in request.path_params:
            class_name = Address.from_string(request.path_params['address']).class_name
            values = get_values_from_response(response)

        if class_name and isinstance(response, dict):
            config = (
                await FrontendModelConfig.objects.all()
                .first(
                    class_name=class_name,
                    _metadata__is_deleted=False,
                    _address__object_version=Versions.LATEST,
                )
                .aexecute()
            )

            if config and config.control:
                response['control'] = populate_frontend_config_with_values(
                    config.control.model_dump(exclude_none=True), values
                )
            else:
                response['control'] = populate_frontend_config_with_values(get_default_control(class_name), values)
