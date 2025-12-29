from amsdal_data.connections.historical.schema_version_manager import AsyncHistoricalSchemaVersionManager, HistoricalSchemaVersionManager

class ClassVersionsMixin:
    """
    Mixin class to manage class versions and related table schemas.
    """
    @staticmethod
    def _register_internal_classes(schema_version_manager: HistoricalSchemaVersionManager | AsyncHistoricalSchemaVersionManager) -> None: ...
    @classmethod
    def register_internal_classes(cls) -> None: ...
    @classmethod
    def aregister_internal_classes(cls) -> None: ...
