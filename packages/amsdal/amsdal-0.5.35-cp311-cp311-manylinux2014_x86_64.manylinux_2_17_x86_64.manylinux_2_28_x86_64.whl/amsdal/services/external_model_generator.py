"""
External Model Generator Service.

Generates ExternalModel classes from external connection schemas.
This allows runtime model generation from external databases without
manual model definition.
"""

from typing import Any
from typing import cast

from amsdal_data.connections.external.base import SchemaIntrospectionProtocol
from amsdal_models.classes.external_model import ExternalModel
from amsdal_models.utils.schema_converter import ExternalSchemaConverter
from amsdal_utils.schemas.schema import ObjectSchema

from amsdal.services.external_connections import ExternalConnectionManager


class ExternalModelGenerator:
    """
    Service for generating ExternalModel classes from external connections.

    This service introspects external database schemas and generates
    corresponding ExternalModel classes that can be used immediately
    for querying the external data.

    Features:
    - Automatic schema introspection
    - Type mapping (SQL types -> Python types)
    - Primary key detection
    - In-memory model class generation
    - No lakehouse schema creation

    Example usage:
        # Generate models for a single table
        generator = ExternalModelGenerator()
        User = generator.generate_model('external_db', 'users')

        # Now use the generated model
        users = User.objects.filter(active=True).execute()

        # Generate models for all tables
        models = generator.generate_models_for_connection('external_db')
        User = models['User']
        Post = models['Post']
    """

    def __init__(self) -> None:
        self._connection_manager = ExternalConnectionManager()
        self._schema_converter = ExternalSchemaConverter()

    def generate_model(
        self,
        connection_name: str,
        table_name: str,
        model_name: str | None = None,
    ) -> type[ExternalModel]:
        """
        Generate an ExternalModel class for a specific table.

        Args:
            connection_name: Name of the external connection
            table_name: Name of the table to generate model for
            model_name: Optional custom model name (defaults to classified table name)

        Returns:
            type[ExternalModel]: Generated model class ready to use

        Raises:
            ValueError: If connection doesn't support schema introspection
            ConnectionError: If connection is not available
            RuntimeError: If model generation fails

        Example:
            generator = ExternalModelGenerator()
            User = generator.generate_model('external_db', 'users')

            # Query using the generated model
            active_users = User.objects.filter(active=True).execute()
        """
        # Get the connection
        connection = self._connection_manager.get_connection(connection_name)

        # Check if connection supports schema introspection
        if not isinstance(connection, SchemaIntrospectionProtocol):  # type: ignore[misc]
            msg = (
                f"Connection '{connection_name}' does not support schema introspection. "
                f'Connection type: {type(connection).__name__}'
            )
            raise ValueError(msg)

        # Get table schema
        table_schema = connection.get_table_schema(table_name)

        # Convert to ObjectSchema
        # Detect connection type and use appropriate converter
        object_schema = self._convert_schema(
            connection=connection,
            table_name=table_name,
            table_schema=table_schema,
            connection_name=connection_name,
        )

        # Generate model class from ObjectSchema
        model_class = self._create_model_class(object_schema, model_name)

        return model_class

    def generate_models_for_connection(
        self,
        connection_name: str,
        table_names: list[str] | None = None,
    ) -> dict[str, type[ExternalModel]]:
        """
        Generate ExternalModel classes for all tables in a connection.

        Args:
            connection_name: Name of the external connection
            table_names: Optional list of specific tables to generate models for.
                        If None, generates models for all tables.

        Returns:
            dict[str, type[ExternalModel]]: Dictionary mapping model names to model classes

        Raises:
            ValueError: If connection doesn't support schema introspection
            ConnectionError: If connection is not available

        Example:
            generator = ExternalModelGenerator()
            models = generator.generate_models_for_connection('external_db')

            # Access generated models
            User = models['User']
            Post = models['Post']
            Comment = models['Comment']

            # Or generate only specific tables
            models = generator.generate_models_for_connection(
                'external_db',
                table_names=['users', 'posts']
            )
        """
        # Get the connection
        connection = self._connection_manager.get_connection(connection_name)

        # Check if connection supports schema introspection
        if not isinstance(connection, SchemaIntrospectionProtocol):  # type: ignore[misc]
            msg = (
                f"Connection '{connection_name}' does not support schema introspection. "
                f'Connection type: {type(connection).__name__}'
            )
            raise ValueError(msg)

        # Get list of tables
        if table_names is None:
            table_names = connection.get_table_names()

        # Generate models for each table
        models: dict[str, type[ExternalModel]] = {}
        for table_name in table_names:
            try:
                model = self.generate_model(connection_name, table_name)
                models[model.__name__] = model
            except Exception as e:
                # Log error but continue with other tables
                print(f"Warning: Failed to generate model for table '{table_name}': {e}")
                continue

        return models

    def _convert_schema(
        self,
        connection: Any,
        table_name: str,
        table_schema: list[dict[str, Any]],
        connection_name: str,
    ) -> ObjectSchema:
        """
        Convert raw table schema to ObjectSchema based on connection type.

        Args:
            connection: The connection object
            table_name: Name of the table
            table_schema: Raw schema data from connection
            connection_name: Name of the connection

        Returns:
            ObjectSchema: Converted schema
        """
        # Detect connection type and use appropriate converter
        connection_type = type(connection).__name__

        if 'sqlite' in connection_type.lower():
            return self._schema_converter.sqlite_schema_to_object_schema(
                table_name=table_name,
                columns=table_schema,
                connection_name=connection_name,
            )

        # For other connection types, try to use generic converter
        # First, try to detect the schema format
        if table_schema and isinstance(table_schema[0], dict):
            # Check if it's SQLite format (has 'cid', 'name', 'type', 'pk', etc.)
            if all(key in table_schema[0] for key in ('cid', 'name', 'type')):
                return self._schema_converter.sqlite_schema_to_object_schema(
                    table_name=table_name,
                    columns=table_schema,
                    connection_name=connection_name,
                )

            # Check if it's PostgreSQL format (has 'column_name', 'data_type', etc.)
            if 'column_name' in table_schema[0] and 'data_type' in table_schema[0]:
                return self._schema_converter.postgres_schema_to_object_schema(
                    table_name=table_name,
                    columns=table_schema,
                    connection_name=connection_name,
                )

            # Try generic converter with format normalization
            normalized_columns = self._normalize_schema_format(table_schema)
            return self._schema_converter.generic_schema_to_object_schema(
                table_name=table_name,
                columns=normalized_columns,
                connection_name=connection_name,
            )

        msg = f'Unknown schema format for connection type: {connection_type}'
        raise ValueError(msg)

    def _normalize_schema_format(self, table_schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalize various schema formats to generic format.

        Converts various schema formats to the format expected by generic_schema_to_object_schema:
        {'name': str, 'type': str, 'nullable': bool, 'primary_key': bool, 'default': Any}
        """
        normalized = []

        for column in table_schema:
            # Try to extract name
            name = column.get('name') or column.get('column_name') or column.get('field')

            # Try to extract type
            col_type = column.get('type') or column.get('data_type') or column.get('field_type') or 'TEXT'

            # Try to extract nullable
            nullable = True
            if 'nullable' in column:
                nullable = column['nullable']
            elif 'is_nullable' in column:
                nullable = column['is_nullable'] in (True, 'YES', 'yes', 1)
            elif 'notnull' in column:
                nullable = column['notnull'] in (False, 0)

            # Try to extract primary key
            pk = column.get('primary_key') or column.get('pk') or False
            if isinstance(pk, int):
                pk = pk > 0

            # Try to extract default
            default = column.get('default') or column.get('dflt_value') or column.get('column_default')

            normalized.append(
                {
                    'name': name,
                    'type': col_type,
                    'nullable': nullable,
                    'primary_key': pk,
                    'default': default,
                }
            )

        return normalized

    def _create_model_class(
        self,
        object_schema: ObjectSchema,
        custom_name: str | None = None,
    ) -> type[ExternalModel]:
        """
        Create an ExternalModel class from ObjectSchema.

        Args:
            object_schema: The schema to create model from
            custom_name: Optional custom model name

        Returns:
            type[ExternalModel]: Generated model class
        """
        # Extract model metadata from schema
        model_name = custom_name or object_schema.title
        table_name = cast(str, object_schema.__table_name__)  # type: ignore[attr-defined]
        connection_name = cast(str, object_schema.__connection__)  # type: ignore[attr-defined]
        pk_fields = getattr(object_schema, '__primary_key__', None)

        # Build class attributes
        class_attrs: dict[str, Any] = {
            '__table_name__': table_name,
            '__connection__': connection_name,
            '__module__': __name__,
        }

        # Add primary key if present
        if pk_fields:
            # For composite keys, use list; for single key, use string
            if len(pk_fields) == 1:
                class_attrs['__primary_key__'] = pk_fields[0]
            else:
                class_attrs['__primary_key__'] = pk_fields

        # Add field annotations from schema properties
        annotations: dict[str, type] = {}
        if object_schema.properties:
            for field_name, field_def in object_schema.properties.items():
                # Map CoreTypes to Python types for annotations
                field_type = self._core_type_to_python_type(getattr(field_def, 'type', 'string'))
                annotations[field_name] = field_type

        class_attrs['__annotations__'] = annotations

        # Create the model class dynamically
        model_class = type(model_name, (ExternalModel,), class_attrs)

        return cast(type[ExternalModel], model_class)

    @staticmethod
    def _core_type_to_python_type(core_type: str) -> type:
        """
        Convert CoreType string to Python type for annotations.

        Args:
            core_type: CoreType value (e.g., 'string', 'integer')

        Returns:
            type: Corresponding Python type
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'date': str,  # Will be string representation
            'datetime': str,  # Will be string representation
            'binary': bytes,
            'array': list,
            'dictionary': dict,
        }
        return type_mapping.get(core_type, str)
