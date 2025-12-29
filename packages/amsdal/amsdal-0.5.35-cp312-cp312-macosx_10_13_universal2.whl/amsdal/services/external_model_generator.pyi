from _typeshed import Incomplete
from amsdal.services.external_connections import ExternalConnectionManager as ExternalConnectionManager
from amsdal_models.classes.external_model import ExternalModel
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from typing import Any

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
    _connection_manager: Incomplete
    _schema_converter: Incomplete
    def __init__(self) -> None: ...
    def generate_model(self, connection_name: str, table_name: str, model_name: str | None = None) -> type[ExternalModel]:
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
    def generate_models_for_connection(self, connection_name: str, table_names: list[str] | None = None) -> dict[str, type[ExternalModel]]:
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
    def _convert_schema(self, connection: Any, table_name: str, table_schema: list[dict[str, Any]], connection_name: str) -> ObjectSchema:
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
    def _normalize_schema_format(self, table_schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalize various schema formats to generic format.

        Converts various schema formats to the format expected by generic_schema_to_object_schema:
        {'name': str, 'type': str, 'nullable': bool, 'primary_key': bool, 'default': Any}
        """
    def _create_model_class(self, object_schema: ObjectSchema, custom_name: str | None = None) -> type[ExternalModel]:
        """
        Create an ExternalModel class from ObjectSchema.

        Args:
            object_schema: The schema to create model from
            custom_name: Optional custom model name

        Returns:
            type[ExternalModel]: Generated model class
        """
    @staticmethod
    def _core_type_to_python_type(core_type: str) -> type:
        """
        Convert CoreType string to Python type for annotations.

        Args:
            core_type: CoreType value (e.g., 'string', 'integer')

        Returns:
            type: Corresponding Python type
        """
