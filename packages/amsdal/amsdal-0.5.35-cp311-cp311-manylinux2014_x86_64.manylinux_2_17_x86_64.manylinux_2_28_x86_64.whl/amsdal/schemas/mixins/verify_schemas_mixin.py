from amsdal_models.errors import AmsdalValidationError
from amsdal_utils.schemas.schema import ObjectSchema


class VerifySchemasMixin:
    """
    Mixin class to verify schemas for uniqueness and property consistency.

    This class provides methods to verify that schemas are unique and that their properties are consistent. It raises
    an `AmsdalValidationError` if any schema is duplicated or if any required or unique property is missing.
    """

    def verify_schemas(
        self,
        type_schemas: list[ObjectSchema],
        core_schemas: list[ObjectSchema],
        contrib_schemas: list[ObjectSchema],
        user_schemas: list[ObjectSchema],
    ) -> None:
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
        self._verify_unique_schemas(type_schemas, core_schemas, contrib_schemas, user_schemas)
        self._verify_properties(type_schemas, core_schemas, contrib_schemas, user_schemas)

    @staticmethod
    def _verify_unique_schemas(
        type_schemas: list[ObjectSchema],
        core_schemas: list[ObjectSchema],
        contrib_schemas: list[ObjectSchema],
        user_schemas: list[ObjectSchema],
    ) -> None:
        _unique_schemas: dict[str, str] = {}

        for source, schemas in (
            ('type_schemas', type_schemas),
            ('core_schemas', core_schemas),
            ('contrib_schemas', contrib_schemas),
            ('user_schemas', user_schemas),
        ):
            for _schema in schemas:
                if _schema.title in _unique_schemas:
                    msg = f"Schema '{source}'.'{_schema.title}' is duplicated (already registered in {_unique_schemas[_schema.title]})."  # noqa: E501
                    raise AmsdalValidationError(msg)

                _unique_schemas[_schema.title] = source

    @staticmethod
    def _verify_properties(
        type_schemas: list[ObjectSchema],
        core_schemas: list[ObjectSchema],
        contrib_schemas: list[ObjectSchema],
        user_schemas: list[ObjectSchema],
    ) -> None:
        all_schemas: list[ObjectSchema] = []
        all_schemas.extend(type_schemas)
        all_schemas.extend(core_schemas)
        all_schemas.extend(contrib_schemas)
        all_schemas.extend(user_schemas)

        for _schema in all_schemas:
            for _field in ['required', 'indexed']:
                for _required_property in getattr(_schema, _field, None) or []:
                    if _required_property not in (_schema.properties or {}):
                        exc_msg = (
                            f'Property {_required_property} marked as {_field} '
                            f"but wasn't found in class schema's properties."
                        )

                        raise AmsdalValidationError(exc_msg)

            for unique in getattr(_schema, 'unique', None) or []:
                for unique_property in unique:
                    if unique_property not in (_schema.properties or {}):
                        exc_msg = (
                            f"Property {unique_property} marked is used in 'unique' "
                            f"but wasn't found in class schema's properties."
                        )

                        raise AmsdalValidationError(exc_msg)
