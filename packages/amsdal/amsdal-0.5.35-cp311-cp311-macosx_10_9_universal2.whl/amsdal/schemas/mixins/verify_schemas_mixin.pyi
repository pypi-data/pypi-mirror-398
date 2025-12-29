from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema

class VerifySchemasMixin:
    """
    Mixin class to verify schemas for uniqueness and property consistency.

    This class provides methods to verify that schemas are unique and that their properties are consistent. It raises
    an `AmsdalValidationError` if any schema is duplicated or if any required or unique property is missing.
    """
    def verify_schemas(self, type_schemas: list[ObjectSchema], core_schemas: list[ObjectSchema], contrib_schemas: list[ObjectSchema], user_schemas: list[ObjectSchema]) -> None:
        """
        Verifies the provided schemas for uniqueness and property consistency.

        This method checks that the provided type, core, contrib, and user schemas are unique and that their properties
        are consistent. It raises an `AmsdalValidationError` if any schema is duplicated or if any required or unique
        property is missing.

        Args:
            type_schemas (list[ObjectSchema]): A list of type schemas to verify.
            core_schemas (list[ObjectSchema]): A list of core schemas to verify.
            contrib_schemas (list[ObjectSchema]): A list of contrib schemas to verify.
            user_schemas (list[ObjectSchema]): A list of user schemas to verify.

        Raises:
            AmsdalValidationError: If any schema is duplicated or if any required or unique property is missing.

        Returns:
            None
        """
    @staticmethod
    def _verify_unique_schemas(type_schemas: list[ObjectSchema], core_schemas: list[ObjectSchema], contrib_schemas: list[ObjectSchema], user_schemas: list[ObjectSchema]) -> None: ...
    @staticmethod
    def _verify_properties(type_schemas: list[ObjectSchema], core_schemas: list[ObjectSchema], contrib_schemas: list[ObjectSchema], user_schemas: list[ObjectSchema]) -> None: ...
