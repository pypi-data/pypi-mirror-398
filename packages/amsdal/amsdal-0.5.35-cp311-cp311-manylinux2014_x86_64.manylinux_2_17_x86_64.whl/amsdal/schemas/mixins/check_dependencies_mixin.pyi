from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema

class CheckDependenciesMixin:
    """
    Mixin class to check dependencies among schemas.

    This class provides methods to check if all dependencies for a given set of schemas are defined. It raises an
    `AmsdalValidationError` if any dependency is not defined.
    """
    def check_dependencies(self, type_schemas: list[ObjectSchema], core_schemas: list[ObjectSchema], contrib_schemas: list[ObjectSchema], user_schemas: list[ObjectSchema]) -> None:
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
    @classmethod
    def _is_enum(cls, _type: TypeData) -> bool: ...
