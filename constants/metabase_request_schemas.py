from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .metabase_schemas import DatasetQuery, MetabaseNativeQuery


class ChartConfig(BaseModel):
    series: Optional[Dict] = Field(default_factory=dict)
    timeline_events: List = Field(default_factory=list)
    query: DatasetQuery | None = None
    display_type: str = Field(alias="display_type")
    native: Optional[MetabaseNativeQuery] = None
    image_base_64: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    timeline_events: Optional[List[Any]] = []
    display_type: Optional[str] = None


class ViewingContext(BaseModel):
    id: Optional[str] = None
    type: str
    query: DatasetQuery | None = None
    error: Optional[str] = None
    sql_engine: Optional[str] = None
    chart_configs: List[ChartConfig] | None = []
    dashboard_image: Optional[str] = None


class UserContext(BaseModel):
    user_is_viewing: List[ViewingContext] | None = []
    current_user_time: datetime | None = None
    capabilities: Optional[List[str]]

class MetabaseContent(BaseModel):
    type: str
    text:str

class Message(BaseModel):
    role: str
    content: list[MetabaseContent]


class MetabaseAgentRequest(BaseModel):
    messages: List[Message]
    model: str ="gpt-4o"
    stream: bool = True
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    tool_choice: Optional[dict] = None
    tools: Optional[List[Any]] = None
    context: Optional[UserContext] = None
    state: Dict = {}
    system:str = ""
    # history: List = Field( default=[])
    user_id: Optional[int] = None
    conversation_id: str = "contersation_id_not_provided"

class DashboardDetails(BaseModel):
    name: str
    data: Dict[str, Any]


class DashboardAnalysisRequest(BaseModel):
    message: str | None = None
    dashboard_data: List[DashboardDetails]
    conversation_id: str


class DashboardDataResponse(BaseModel):
    success: bool
    message: str | None = None
    data:str | None = None
