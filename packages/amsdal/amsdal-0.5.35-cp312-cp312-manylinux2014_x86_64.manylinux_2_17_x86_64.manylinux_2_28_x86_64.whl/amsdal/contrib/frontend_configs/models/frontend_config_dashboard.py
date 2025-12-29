from typing import Any
from typing import ClassVar
from typing import Literal
from typing import Optional

from amsdal_models.classes.model import Model
from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class FrontendConfigDashboardQueryParams(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    field: str = Field(..., description='Field name for the query parameter')
    operator: str = Field(..., description='Operator for the query parameter')
    value: Optional[Any] = Field(None, description='Value for the query parameter')


class FrontendConfigDashboardDataSource(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    type: Literal['class', 'transaction']
    entity_name: str = Field(..., description='Name of the entity or transaction')
    query_params: list[FrontendConfigDashboardQueryParams] | None = Field(
        None, description='List of query parameters for filtering data (for class type)'
    )
    body: Any = Field(None, description='Request body for transaction data source (for transaction type)')


class FrontendConfigDashboardElement(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    type: Literal['section', 'grid', 'grid_col', 'chart', 'table']
    chart_type: str | None = Field(None, description='Type of chart (for chart elements)')
    columns: int | None = Field(None, description='Number of columns for grid layout')
    rows: int | None = Field(None, description='Number of rows for grid layout')
    title: str | None = Field(None, description='Title of the dashboard element')
    elements: list['FrontendConfigDashboardElement'] | None = Field(
        None, description='Nested dashboard elements for section or grid types'
    )
    data_source: FrontendConfigDashboardDataSource | None = Field(
        None, description='Data source configuration for chart or table elements'
    )


class FrontendConfigDashboard(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    title: str = Field(..., description='Title of the dashboard')
    elements: list[FrontendConfigDashboardElement] = Field(..., description='List of dashboard elements')
