import contextlib
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import Union
from typing import get_origin

from amsdal_models.classes.model import LegacyModel
from amsdal_models.classes.model import Model
from amsdal_utils.models.data_models.reference import Reference
from polyfactory.factories.base import BuildContext
from polyfactory.field_meta import FieldMeta
from polyfactory.field_meta import Null

try:
    import polyfactory.factories.pydantic_factory as factories
except ImportError:
    _msg = '"polyfactory" package is required for using this module. Use "pip install amsdal[factory]" to install it.'
    raise ImportError(_msg) from None


T = TypeVar('T', bound=Model)


class AmsdalFactory(Generic[T], factories.ModelFactory[T]):
    __is_base_factory__ = True

    @classmethod
    def get_field_value(
        cls,
        field_meta: FieldMeta,
        field_build_parameters: Any | None = None,
        build_context: BuildContext | None = None,
    ) -> Any:
        if get_origin(field_meta.annotation) is Union and field_meta.default is Null:
            with contextlib.suppress(TypeError):
                is_class_definition = any(
                    issubclass(arg, LegacyModel) for arg in field_meta.annotation.__args__
                ) and any(issubclass(arg, Reference) for arg in field_meta.annotation.__args__)
                is_optional = any(issubclass(arg, type(None)) for arg in field_meta.annotation.__args__)

                if is_optional:
                    field_meta.annotation = type(None)
                elif is_class_definition:
                    for _type in field_meta.annotation.__args__:
                        if not issubclass(_type, LegacyModel | type(None) | Reference):
                            field_meta.annotation = _type

        return super().get_field_value(field_meta, field_build_parameters, build_context)
