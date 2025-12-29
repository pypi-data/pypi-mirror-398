from typing import Any
from typing import ClassVar
from typing import Literal

from amsdal_models.builder.validators.options_validators import validate_options
from amsdal_utils.models.enums import ModuleType
from pydantic import Field
from pydantic import field_validator

from amsdal.contrib.frontend_configs.models.frontend_config_skip_none_base import *  # noqa: F403

__all__ = [
    'ActionType',
    'ChangeContextAction',
    'FrontendConfigControlAction',
    'InvokeAction',
    'SaveAction',
    'UpdateValueAction',
]


class FrontendConfigControlAction(FrontendConfigSkipNoneBase):  # noqa: F405
    """Navigation action for form controls (backward compatible)."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    action: str = Field(title='Action')
    text: str = Field(title='Text')
    type: str = Field(title='Type')
    dataLayerEvent: str | None = Field(None, title='Data Layer Event')  # noqa: N815
    activator: str | None = Field(None, title='Activator')
    icon: str | None = Field(None, title='Icon')

    @field_validator('type')
    @classmethod
    def validate_value_in_options_type(cls: type, value: Any) -> Any:  # type: ignore # noqa: A003
        return validate_options(value, options=['action-button', 'arrow-next', 'arrow-prev', 'text-next', 'text-prev'])

    @field_validator('action', mode='after')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """
        Validates the action string to ensure it is one of the allowed values.

        This method checks if the action string starts with 'navigate::' or is one of the predefined
        actions. If the action string is invalid, it raises a ValueError.

        Args:
            cls: The class this method is attached to.
            v (str): The action string to validate.

        Returns:
            str: The validated action string.

        Raises:
            ValueError: If the action string is not valid.
        """
        if not v.startswith('navigate::') and v not in [
            'goPrev',
            'goNext',
            'goNextWithSubmit',
            'submit',
            'submitWithDataLayer',
        ]:
            msg = 'Action must be one of: goPrev, goNext, goNextWithSubmit, submit, submitWithDataLayer, navigate::{string}'  # noqa: E501
            raise ValueError(msg)
        return v


class UpdateValueAction(FrontendConfigSkipNoneBase):  # noqa: F405
    """Action to update a field value (used in onSuccess callbacks)."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    type: Literal['update_value'] = Field(title='Type')
    field_id: str = Field(title='Field ID')
    value: Any = Field(title='Value')


class InvokeAction(FrontendConfigSkipNoneBase):  # noqa: F405
    """Action to invoke an API endpoint."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    type: Literal['invoke'] = Field(title='Type')
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] = Field(title='HTTP Method')
    url: str = Field(title='URL')
    headers: dict[str, str] | None = Field(None, title='Headers')
    body: dict[str, Any] | None = Field(None, title='Body')
    onSuccess: list['ActionType'] | None = Field(None, title='On Success Actions')  # noqa: N815
    onError: list['ActionType'] | None = Field(None, title='On Error Actions')  # noqa: N815


class ChangeContextAction(FrontendConfigSkipNoneBase):  # noqa: F405
    """Action to change the context."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    type: Literal['change_context'] = Field(title='Type')
    context: dict[str, Any] = Field(title='Context')


class SaveAction(FrontendConfigSkipNoneBase):  # noqa: F405
    """Action to save data."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    type: Literal['save'] = Field(title='Type')


# Union type for all action types - discriminated by 'type' field
ActionType = FrontendConfigControlAction | InvokeAction | UpdateValueAction | ChangeContextAction | SaveAction

# Rebuild model to handle forward references
InvokeAction.model_rebuild()
