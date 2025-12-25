from enum import Enum
from typing import Any, List, Optional, Union, Dict, Literal, Annotated

from agent_types.common import (
    Intent,
    Observation,
    Plan,
    SessionMemory,
    SystemMemory,
    SystemProfile,
    Tool,
)
from pydantic import BaseModel, Field

from fance_types.common import Citation, SKUCard
from fance_types.product_search.common import FrontendFilterConditions, RecommendSearchResponse

class Event(str, Enum):
    product_compare = "product_compare"
    click_article = "click_article"
    show_articles = "show_articles"
    click_product = "click_product"
    show_products = "show_products"

class ResponseType(str, Enum):
    text = "text"
    decomposition = "decomposition"
    options = "options"
    recommendations = "recommendations"
    comparison_table = "comparison_table"
    product_search_button = "product_search_button"

# Tool type string literals
ToolType = Literal[
    "product_knowledge_search",
    "domain_general_knowledge_search",
    "compare_knowledge_retrieval",
    "web_search",
    "query_search",
    "recommend_search"
]

class ToolResult(BaseModel):
    """Base class for tool results"""
    tool_type: str # 工具名称
    tool_call_id: str # 工具调用id
    title: str = "" # 执行标题
    description: str = "" # 执行描述
    query_list: Optional[List[str]] = None # 知识/联网搜索用的query参数列表
    index: int = 0 # 这个turn第几个执行的工具
    tool_execution_index: int = 0 # 这个turn第几个执行的这种工具

class QuerySearchResponseToolResult(ToolResult):
    tool_type: Literal["query_search"] = "query_search"
    title: str = "Product Search"
    sku_cards: Optional[List[SKUCard]] = None
    frontend_filter_conditions: Optional[FrontendFilterConditions] = None
    tag_value: Optional[str] = None

class RecommendSearchToolResult(ToolResult):
    tool_type: Literal["recommend_search"] = "recommend_search"
    title: str = "Product Search"
    sku_cards: Optional[List[SKUCard]] = None
    product_search_response: Optional[RecommendSearchResponse] = None


class ProductKnowledgeSearchToolResult(ToolResult):
    tool_type: Literal["product_knowledge_search"] = "product_knowledge_search"
    title: str = "Knowledge Search"
    citations: Optional[List[Citation]] = None

class DomainGeneralKnowledgeSearchToolResult(ToolResult):
    tool_type: Literal["domain_general_knowledge_search"] = "domain_general_knowledge_search"
    title: str = "Knowledge Search"
    citations: Optional[List[Citation]] = None

class CompareKnowledgeRetrievalToolResult(ToolResult):
    tool_type: Literal["compare_knowledge_retrieval"] = "compare_knowledge_retrieval"
    title: str = "Knowledge Search"
    citations: Optional[List[Citation]] = None

class WebSearchToolResult(ToolResult):
    tool_type: Literal["web_search"] = "web_search"
    title: str = "Web Search"
    citations: Optional[List[Citation]] = None

class OptionItem(BaseModel):
    key: str = Field(description="Logical key representing the options list.")
    options: List[str] = Field(description=("Array of option strings (2-5)."))

class OptionsList(BaseModel):
    options_list: List[OptionItem] = Field(description="List of options for user to choose from", default=None)

class ChatRequestMetaData(BaseModel):
    options: Optional[OptionsList] = Field(description="options_list: 当用户选择选项卡的时候传入", default=None)

class ChatRequest(BaseModel):
    """Workflow execution request"""
    uid: str = Field(..., description="User ID")
    query: str = Field(..., description="User query to process")
    session_id: str = Field(..., description="Session ID")
    turn_id: int = Field(..., description="Turn ID")
    metadata: Optional[ChatRequestMetaData] = Field(
        description="前端传入的结构化数据", default_factory=ChatRequestMetaData
    )
    event: Optional[Event] = Field(description="事件类型", default=None)

class ChatResponseMetaData(BaseModel):
    response_type: Optional[ResponseType] = Field(description="回复类型， 用来区分纯文本和其它类型的xml卡片输出", default=None)
    tool_result: Optional[Annotated[Union[
        QuerySearchResponseToolResult,
        RecommendSearchToolResult,
        ProductKnowledgeSearchToolResult,
        DomainGeneralKnowledgeSearchToolResult,
        CompareKnowledgeRetrievalToolResult,
        WebSearchToolResult
    ], Field(discriminator='tool_type', description="工具执行结果输出")]] = None

class ChatResponse(BaseModel):
    """Workflow execution response"""

    response_text: Optional[str] = Field(description="Generated response", default=None)
    metadata: Optional[ChatResponseMetaData] = Field(
        description="Meta data", default_factory=ChatResponseMetaData
    )
    citations: Optional[List[Citation]] = Field(description="Citations", default=None)
    scene: str = Field(description="场景：eg. product_compare", default=None)

class Context(BaseModel):
    """Workflow context shared between nodes."""

    session_id: str = None
    turn_id: int = 1
    trace_id: str = None
    query: str = None
    rewrite_query: Optional[str] = None
    intent: Optional[Union[Intent, List[Intent]]] = None
    tools: List[Tool] = []
    system_profile: Optional[SystemProfile] = None
    system_memory: Optional[SystemMemory] = None
    session_memory: Optional[SessionMemory] = None
    planning_system_memory: Optional[SystemMemory] = None
    plan: Optional[Union[Plan, List[Plan]]] = None
    finished: bool = False
    observations: List[Observation] = []
    response: Optional[str] = None
    metadata: Optional[dict] = {}
    default_args: Optional[dict] = {}
    history_chat_type: Optional[str] = None
    tool_execution_count: int = 0
    tool_execution_count_by_name: Dict[str, int] = {}
    tool_results: List[ToolResult] = []