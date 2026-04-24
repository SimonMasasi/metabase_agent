from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    COMBO = "combo"
    WATERFALL = "waterfall"
    SCATTER = "scatter"
    FUNNEL = "funnel"
    PIVOT = "pivot"
    TABLE = "table"


class MetabaseField(BaseModel):
    field_id: int
    base_type: str


class MetabaseAggregation(BaseModel):
    type: str
    field: Optional[MetabaseField] = None


class MetabaseQuery(BaseModel):
    source_table: int | str = Field(default=None)
    breakout: List[Any] = None
    limit: Optional[int] = None
    order_by: Optional[List[List[str]]] = None
    aggregation: Optional[List[Any]] = None
    joins: Optional[List[Any]] = None


class MetabaseNativeQuery(BaseModel):
    template_args: Dict = Field(default_factory=dict)
    query: str


class DatasetQuery(BaseModel):
    database: int | str = None
    type: str = "query"
    query: Optional[MetabaseQuery] | None = None
    native: Optional[MetabaseNativeQuery] | None = None


class VisualizationSettings(BaseModel):
    """Visualization settings for the chart"""

    graph_type: str = Field(default="bar", alias="graph.type")
    graph_display: str = Field(default="line", alias="graph.display")
    column_settings: Optional[Dict] = Field(default=None, alias="graph.column_settings")
    colors: Optional[Dict] = Field(default=None, alias="graph.colors")
    series_settings: Optional[Dict] = Field(default=None, alias="graph.series_settings")


class MetabaseQuestion(BaseModel):
    dataset_query: DatasetQuery
    display: ChartType
    display_is_locked: bool = Field(default=True, alias="displayIsLocked")
    parameters: List = Field(default=[])
    visualization_settings: Optional[VisualizationSettings] = Field(
        alias="visualization_settings"
    )
    type: str = "question"
