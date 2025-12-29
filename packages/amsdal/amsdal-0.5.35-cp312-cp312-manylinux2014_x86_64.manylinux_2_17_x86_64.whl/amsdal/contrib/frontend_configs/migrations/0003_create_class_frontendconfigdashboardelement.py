from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigDashboard",
            new_schema={
                "title": "FrontendConfigDashboard",
                "required": ["title", "elements"],
                "properties": {
                    "title": {"type": "string", "title": "Title", "description": "Title of the dashboard"},
                    "elements": {
                        "type": "array",
                        "items": {"type": "FrontendConfigDashboardElement", "title": "FrontendConfigDashboardElement"},
                        "title": "Elements",
                        "description": "List of dashboard elements",
                    },
                },
                "storage_metadata": {
                    "table_name": "FrontendConfigDashboard",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigDashboardElement",
            new_schema={
                "title": "FrontendConfigDashboardElement",
                "required": ["type"],
                "properties": {
                    "type": {
                        "type": "string",
                        "options": [
                            {"key": "section", "value": "section"},
                            {"key": "grid", "value": "grid"},
                            {"key": "grid_col", "value": "grid_col"},
                            {"key": "chart", "value": "chart"},
                            {"key": "table", "value": "table"},
                        ],
                        "title": "Type",
                        "enum": ["section", "grid", "grid_col", "chart", "table"],
                    },
                    "chart_type": {
                        "type": "string",
                        "title": "Chart Type",
                        "description": "Type of chart (for chart elements)",
                    },
                    "columns": {
                        "type": "integer",
                        "title": "Columns",
                        "description": "Number of columns for grid layout",
                    },
                    "rows": {"type": "integer", "title": "Rows", "description": "Number of rows for grid layout"},
                    "title": {"type": "string", "title": "Title", "description": "Title of the dashboard element"},
                    "elements": {
                        "type": "array",
                        "items": {"type": "FrontendConfigDashboardElement", "title": "FrontendConfigDashboardElement"},
                        "title": "Elements",
                        "description": "Nested dashboard elements for section or grid types",
                    },
                    "data_source": {
                        "type": "FrontendConfigDashboardDataSource",
                        "title": "FrontendConfigDashboardDataSource",
                        "description": "Data source configuration for chart or table elements",
                    },
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {
                    "table_name": "FrontendConfigDashboardElement",
                    "db_fields": {},
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigDashboardQueryParams",
            new_schema={
                "title": "FrontendConfigDashboardQueryParams",
                "required": ["field", "operator"],
                "properties": {
                    "field": {"type": "string", "title": "Field", "description": "Field name for the query parameter"},
                    "operator": {
                        "type": "string",
                        "title": "Operator",
                        "description": "Operator for the query parameter",
                    },
                    "value": {"type": "anything", "title": "Value", "description": "Value for the query parameter"},
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {
                    "table_name": "FrontendConfigDashboardQueryParams",
                    "db_fields": {},
                    "foreign_keys": {},
                },
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="FrontendConfigDashboardDataSource",
            new_schema={
                "title": "FrontendConfigDashboardDataSource",
                "required": ["type", "entity_name"],
                "properties": {
                    "type": {
                        "type": "string",
                        "options": [{"key": "class", "value": "class"}, {"key": "transaction", "value": "transaction"}],
                        "title": "Type",
                        "enum": ["class", "transaction"],
                    },
                    "entity_name": {
                        "type": "string",
                        "title": "Entity Name",
                        "description": "Name of the entity or transaction",
                    },
                    "query_params": {
                        "type": "array",
                        "items": {
                            "type": "FrontendConfigDashboardQueryParams",
                            "title": "FrontendConfigDashboardQueryParams",
                        },
                        "title": "Query Params",
                        "description": "List of query parameters for filtering data (for class type)",
                    },
                    "body": {
                        "type": "anything",
                        "title": "Body",
                        "description": "Request body for transaction data source (for transaction type)",
                    },
                },
                "meta_class": "TypeMeta",
                "storage_metadata": {
                    "table_name": "FrontendConfigDashboardDataSource",
                    "db_fields": {},
                    "foreign_keys": {},
                },
            },
        ),
    ]
