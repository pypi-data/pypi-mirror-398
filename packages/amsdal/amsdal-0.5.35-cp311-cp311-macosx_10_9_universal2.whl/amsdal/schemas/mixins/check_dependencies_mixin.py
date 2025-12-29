from amsdal_models.errors import AmsdalValidationError
from amsdal_utils.models.data_models.core import DictSchema
from amsdal_utils.models.data_models.core import LegacyDictSchema
from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.schemas.schema import ObjectSchema


class CheckDependenciesMixin:
    """
    Mixin class to check dependencies among schemas.

    This class provides methods to check if all dependencies for a given set of schemas are defined. It raises an
    `AmsdalValidationError` if any dependency is not defined.
    """

    def check_dependencies(
        self,
        type_schemas: list[ObjectSchema],
        core_schemas: list[ObjectSchema],
        contrib_schemas: list[ObjectSchema],
        user_schemas: list[ObjectSchema],
    ) -> None:
        """
        Checks if all dependencies for the given schemas are defined.

        This method verifies that all dependencies for the provided type, core, contrib, and user schemas are defined.
        If any dependency is not defined, it raises an `AmsdalValidationError`.

        Args:
            type_schemas (list[ObjectSchema]): A list of type schemas to check.
            core_schemas (list[ObjectSchema]): A list of core schemas to check.
            contrib_schemas (list[ObjectSchema]): A list of contrib schemas to check.
            user_schemas (list[ObjectSchema]): A list of user schemas to check.

        Raises:
            AmsdalValidationError: If any dependency is not defined.

        Returns:
            None
        """
        _defined_schemas: set[str] = {
            *[schema.title.lower() for schema in type_schemas],
            *[schema.title for schema in core_schemas],
            *[schema.title for schema in contrib_schemas],
            *[schema.title for schema in user_schemas],
        }
        _defined_schemas.update(
            {
                CoreTypes.NUMBER,
                CoreTypes.INTEGER,
                CoreTypes.STRING,
                CoreTypes.BOOLEAN,
                CoreTypes.DICTIONARY,
                CoreTypes.ARRAY,
                CoreTypes.ANYTHING,
                CoreTypes.BINARY,
                CoreTypes.OBJECT,
                CoreTypes.DATETIME,
                CoreTypes.DATE,
            }
        )
        all_schemas: list[ObjectSchema] = []
        all_schemas.extend(type_schemas)
        all_schemas.extend(core_schemas)
        all_schemas.extend(contrib_schemas)
        all_schemas.extend(user_schemas)

        for source, schemas in (
            ('type_schemas', type_schemas),
            ('core_schemas', core_schemas),
            ('contrib_schemas', contrib_schemas),
            ('user_schemas', user_schemas),
        ):
            for _schema in schemas:
                for _dependency in self.get_dependency_type_names(_schema):
                    _dependencies = [_dependency]
                    if '|' in _dependency:
                        _dependencies = [dep.strip() for dep in _dependency.split('|')]

                    for _d in _dependencies:
                        if _d not in _defined_schemas:
                            exc_msg = f'Class {_d} ({source}) is undefined! This class is set as dependency for {_schema.title}'  # noqa: E501
                            raise AmsdalValidationError(exc_msg)

    @classmethod
    def get_dependency_type_names(cls, schema: ObjectSchema) -> set[str]:
        """
        Returns a set of dependency type names for the given schema.

        This method extracts and returns a set of type names that the given schema depends on. It includes the schema's
        own type, the types of its properties, and the types of items within array or dictionary properties.

        Args:
            schema (ObjectSchema): The schema for which to get dependency type names.

        Returns:
            set[str]: A set of dependency type names for the given schema.
        """
        _dependencies: set[str] = {
            schema.type,
        }

        for _property in schema.properties.values() if schema.properties else []:
            if cls._is_enum(_property):
                continue

            _dependencies.add(_property.type)

            if _property.type == CoreTypes.ARRAY and isinstance(_property.items, TypeData):
                if not cls._is_enum(_property.items):
                    _dependencies.add(_property.items.type)
            elif _property.type == CoreTypes.DICTIONARY:
                if isinstance(_property.items, LegacyDictSchema):
                    _dependencies.add(_property.items.key_type)
                    _dependencies.add(_property.items.value_type)
                elif isinstance(_property.items, DictSchema):
                    if not cls._is_enum(_property.items.key):
                        _dependencies.add(_property.items.key.type)
                    if not cls._is_enum(_property.items.value):
                        _dependencies.add(_property.items.value.type)

        # remove self reference
        _dependencies.discard(schema.title)

        return _dependencies

    @classmethod
    def _is_enum(cls, _type: TypeData) -> bool:
        return bool(hasattr(_type, 'enum') and _type.enum and _type.options)
