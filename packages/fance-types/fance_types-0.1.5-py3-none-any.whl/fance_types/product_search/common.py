#!/usr/bin/env python3

from typing import Any, Dict, List, Optional, Union

from agent_types.common import ToolResponse, Request
from libentry.mcp.service import RunServiceConfig
from pydantic import BaseModel, Field, field_validator

from fance_types.common import SKU
from fance_types.common import SKUCard as SKUCardModel


class ProductSearchServiceConfig(RunServiceConfig):
    """ProductSearchService配置类，包含所有可配置参数"""

    port: int = Field(description="服务端口")
    # 缓存配置
    cache_maxsize: int = Field(default=128, description="筛选选项缓存最大大小")
    cache_ttl: int = Field(
        default=3600, description="筛选选项缓存TTL（秒），默认30分钟"
    )

    # 服务端点配置
    dataloader_url: str = Field(
        default="", description="数据加载器URL"
    )

    # Elasticsearch配置
    index_name: str = Field(default="fance_skus_v1", description="ES索引名称")

    # 调度器配置
    update_interval: int = Field(
        default=3600, description="定时更新间隔（秒），默认1小时"
    )

    # 搜索配置
    recommend_size: int = Field(default=15, description="推荐搜索返回数量")
    query_search_size: int = Field(default=15, description="查询搜索默认返回数量")

    # 批量操作配置
    batch_size: int = Field(default=1000, description="SKU数据批量更新大小")

    # ES Scroll配置
    scroll_timeout: str = Field(default="5m", description="ES scroll超时时间")
    scroll_size: int = Field(default=1000, description="ES scroll每次获取的文档数量")


# ============= Filter Options 相关数据模型 =============


class FilterOptionValue(BaseModel):
    """筛选选项值"""

    value: str = Field(description="选项值")
    label: str = Field(description="显示标签")


class FilterCascadeOption(BaseModel):
    """级联筛选选项（用于品牌级联结构）"""

    value: str = Field(description="选项值")
    label: str = Field(description="显示标签")
    children: Optional[List["FilterCascadeOption"]] = Field(
        description="子级选项", default=None
    )


class FilterRangeOptions(BaseModel):
    """数值范围选项"""

    min: float = Field(description="最小值")
    max: float = Field(description="最大值")


class FilterFieldOption(BaseModel):
    """单个筛选字段的选项"""

    name: str = Field(description="字段名称")
    label: str = Field(description="字段显示标签")
    types: str = Field(
        description="字段类型：cascader（级联选择器）、select（下拉选择器）、slider（滑动条）"
    )
    options: Union[
        List[FilterOptionValue], List[FilterCascadeOption], FilterRangeOptions
    ] = Field(
        description="选项列表（枚举字段）、级联选项列表（品牌字段）或范围对象（数值字段）"
    )


class FilterOptionsRequest(BaseModel):
    """获取筛选选项请求参数"""

    fields: Optional[List[str]] = Field(
        description="需要获取选项的字段列表，支持的字段：brand, screen, cpu, gpu, storage, ram, weight, price。如果为空则返回所有支持的字段",
        default=None,
        examples=[["brand", "cpu", "price"], ["brand"], None],
    )
    top_k: int = Field(
        description="枚举字段返回的最大选项数量，默认10000（相当于无限制）。仅对枚举字段有效，数值字段不受此参数影响",
        default=10000,
        min=1,
        max=10000,
    )


class FilterOptionsResponse(BaseModel):
    """获取筛选选项响应"""

    filter_options: List[FilterFieldOption] = Field(
        description="筛选选项列表",
        examples=[
            [
                {
                    "name": "brand",
                    "label": "Brand",
                    "options": [
                        {"value": "Dell", "label": "Dell"},
                        {"value": "Lenovo", "label": "Lenovo"},
                    ],
                },
                {
                    "name": "price",
                    "label": "Price Range",
                    "options": {"min": 190.0, "max": 7561.03},
                },
            ]
        ],
    )


# ============= Filter Condition 内部搜索相关数据模型 =============
class BrandCondition(BaseModel):
    """
    Unless the brand/sub brand/series is specifically mentioned, try to use the model field as much as possible to achieve better matching results
    """

    brand: Optional[str] = Field(
        default=None,
        description="Name of brand, e.g. 'Lenovo', 'Dell', 'Apple', 'ASUS', 'HP'",
        title="Brand",
    )
    sub_brand: Optional[str] = Field(
        default=None,
        description="Name of sub brand, e.g. 'ThinkPad', 'Inspiron', 'Zenbook', 'MacBook'",
        title="Sub Brand",
    )
    series: Optional[str] = Field(
        default=None,
        description="Name of series, e.g. 'T Series', 'X1 Series', 'Pro', 'Air'",
        title="Series",
    )
    model: Optional[str] = Field(
        default=None,
        description="Name of model, e.g. 'Lenovo Yoga Slim 7', 'Lenovo ThinkPad P16 Gen 3'",
        title="Model",
    )


class CPUCondition(BaseModel):
    cpu_vendor: Optional[str] = Field(
        default=None,
        description="Name of CPU vendor, e.g. 'Intel', 'AMD'",
        title="CPU Vendor",
    )
    cpu_series: Optional[str] = Field(
        default=None,
        description="Name of CPU series, e.g. 'Core i7', 'Ryzen 7', 'Core Ultra 9'",
        title="CPU Series",
    )
    cpu_model: Optional[str] = Field(
        default=None,
        description="Name of CPU model, e.g. '5800X'",
        title="CPU Model",
    )
    cpu_full_name: Optional[str] = Field(
        default=None,
        description="Full name of CPU, e.g. 'Intel Core i7-11600K', 'AMD Ryzen 7-5800X'",
        title="CPU Full Name",
    )
    # 是否为最低要求
    is_minimum_requirement: Optional[bool] = Field(
        default=False,
        description="Whether the CPU is the minimum requirement",
        title="Is Minimum Requirement",
    )


class GPUCondition(BaseModel):
    gpu_type: Optional[str] = Field(
        default=None,
        description="GPU type, i.e. 'Integrated', 'Dedicated'",
        title="GPU Type",
    )
    gpu_series: Optional[str] = Field(
        default=None,
        description="Name of GPU series, e.g. 'Nvidia RTX 50', 'AMD Radeon RX'",
        title="GPU Series",
    )
    gpu_model: Optional[str] = Field(
        default=None,
        description="Name of GPU model, e.g. 'NVIDIA GeForce RTX 5080'",
        title="GPU Model",
    )
    is_minimum_requirement: Optional[bool] = Field(
        default=False,
        description="Whether the GPU is the minimum requirement",
        title="Is Minimum Requirement",
    )


class OSCondition(BaseModel):
    os_family: Optional[str] = Field(
        default=None,
        description="Name of OS vendor, e.g. 'Windows', 'Mac OS', 'Chrome OS'",
        title="OS Vendor",
    )
    os_model: Optional[str] = Field(
        default=None,
        description="Name of OS series, e.g. 'Windows 11 Home'",
        title="OS Series",
    )


class FilterConditions(BaseModel):
    """
    Filtering syntax:
    - Use 'List' to specify multiple acceptable values (logical OR).
      e.g. brand=[BrandCondition(brand='Dell'), BrandCondition(brand='ASUS'), BrandCondition(brand='Lenovo')] → matches any of them.
    - Single item is also supported.
    - Use '-' to specify a numeric or comparable range.
      e.g. price=['800-1200'] → price between 800 and 1200 (inclusive).
    - Use 'is_minimum_requirement' to specify whether the CPU/GPU condition is the minimum requirement.
      e.g. cpu=[CPUCondition(cpu_model='Intel Core i7', is_minimum_requirement=True)] → matches CPUs better than Intel Core i7.
    - Use '-None'/ 'None-' to specify 'greater than'/'less than' for numeric or comparable fields.
      e.g. price=['800-None'] → price greater than 800.
      e.g. price=['None-1200'] → price less than 1200.
    - above syntax can be combined in the list.
    """

    brand: Optional[List[BrandCondition]] = Field(
        default=None,
        description="List of brand conditions. Unless the brand/sub brand/series is specifically mentioned, try to use the model field as much as possible to achieve better matching results",
        title="Brands",
    )
    cpu: Optional[List[CPUCondition]] = Field(
        default=None,
        description="List of CPU conditions, also use cpu_full_name first",
        title="CPUs",
    )
    gpu: Optional[List[GPUCondition]] = Field(
        default=None,
        description="List of GPU conditions",
        title="GPUs",
    )
    operating_system: Optional[List[OSCondition]] = Field(
        default=None,
        description="List of OS conditions",
        title="OSes",
    )
    screen_size: Optional[List[str]] = Field(
        default=None,
        description="Screen Size Conditions.",
        examples=[["13.0-13.9", "16.0-None"]],
    )
    storage: Optional[List[str]] = Field(
        default=None,
        description="Storage capacity in GB. ",
        examples=[["512-1024", "2048-None"]],
    )
    ram: Optional[List[str]] = Field(
        default=None,
        description="RAM capacity in GB.",
        examples=[["8-16", "32-None"]],
    )
    price: Optional[List[str]] = Field(
        default=None,
        description="Price range in USD. ",
        examples=[["1000-2000", "2000-None"]],
    )
    weight: Optional[List[str]] = Field(
        default=None,
        description="Weight range in pounds.",
        examples=[["2.5-3.5", "3.5-None"]],
    )
    year: Optional[List[str]] = Field(
        default=None,
        description="Release year."
        "If user mentions phrases like 'latest' or 'newest', use current year.",
        examples=[["2022-2025", "2025"]],
    )
    color: Optional[List[str]] = Field(
        default=None,
        description="Color(s)",
        examples=[["black", "silver", "gray"]],
    )
    user_group: Optional[List[str]] = Field(
        default=None,
        description="User groups"
        "Available groups: office_workers, creators, gamers, developers, students, home_users.",
        examples=[["gamers", "creators", "developers"]],
    )

    def model_dump(self, **kwargs):
        # 如果 exclude_none 没有在 kwargs 中指定，则设置为 True
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def __str__(self):
        return str(self.model_dump())

    def __hash__(self):
        """支持 lru_cache 的哈希方法"""
        # 将所有字段值转换为可哈希的元组
        values = []
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                # 处理列表类型（转换为元组）
                if isinstance(value, list):
                    # 如果列表中包含对象，需要转换为可哈希的格式
                    hashable_list = []
                    for item in value:
                        if hasattr(item, "model_dump"):
                            # 对于 Pydantic 模型，转换为元组
                            hashable_list.append(
                                tuple(sorted(item.model_dump().items()))
                            )
                        else:
                            hashable_list.append(item)
                    values.append((field_name, tuple(hashable_list)))
                else:
                    values.append((field_name, value))
        return hash(tuple(sorted(values)))

    @field_validator(
        "price",
        "screen_size",
        "weight",
        "ram",
        "storage",
        "year",
        mode="before",
    )
    @classmethod
    def normalize_range_expression(cls, value):
        """规范化范围表达式：支持简写形式（-1500 或 3-）和 ~ 分隔符"""
        if value is None:
            return value

        # 如果是列表，递归处理每个元素
        if isinstance(value, list):
            return [cls.normalize_range_expression(item) for item in value]

        # 处理单个字符串值
        if isinstance(value, str):
            # 将 ~ 替换为 -
            if "~" in value:
                value = value.replace("~", "-")

            # 处理以-开头的情况（如 -1500 -> None-1500）
            if "-" in value:
                if value.startswith("-") and not value.startswith("None-"):
                    return f"None{value}"
                # 处理以-结尾的情况（如 3- -> 3-None）
                elif value.endswith("-") and not value.endswith("-None"):
                    return f"{value}None"

        return value

    # class Config:
    #     extra = "allow"


class FilterSearchRequest(BaseModel):
    model_config = {"populate_by_name": True}  # 允许同时使用字段名和别名

    filter_conditions: FilterConditions = Field(
        description="Recommend filter profile.",
        default=None,
        examples=[
            {
                "series": "ThinkPad X1 Carbon",
                "brand": "Lenovo",
            }
        ],
    )
    size: int = Field(
        description="Maximum number of items to return", default=200, min=10, max=200
    )
    page: int = Field(description="Page number (1-based)", default=1, min=1)
    up_down_status: Optional[bool] = Field(
        description="Whether to filter by up/down status", default=True
    )
    sort_by: Optional[str] = Field(
        description="Sorting order: 'price_asc' for price ascending, 'price_desc' for price descending, 'popularity' for balanced release time and popularity",
        default="popularity",
        enum=["price_asc", "price_desc", "popularity"],
        alias="tag_value",
    )

    def __hash__(self):
        """支持 lru_cache 的哈希方法"""
        # 将所有字段值转换为可哈希的元组
        values = []
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                # 对于 FilterConditions 对象，使用其哈希值
                if isinstance(value, FilterConditions):
                    values.append((field_name, hash(value)))
                else:
                    values.append((field_name, value))
        return hash(tuple(sorted(values)))


class PaginationInfo(BaseModel):
    """分页信息"""

    current_page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total_items: int = Field(description="总条目数")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class ExtraSKU(SKU):
    class Config:
        extra = "allow"


class InternalSearchResponse(BaseModel):
    """SKU搜索响应"""

    skus: List[ExtraSKU] = Field(description="搜索到的SKU对象列表")
    pagination: Optional[PaginationInfo] = Field(description="分页信息", default=None)


class FilterSearchResponse(BaseModel):
    """筛选搜索响应，包含SKU卡片信息"""

    sku_cards: List[SKUCardModel] = Field(description="SKU卡片信息列表")
    pagination: Optional[PaginationInfo] = Field(description="分页信息", default=None)


# ============= Recommend Search 相关数据模型 =============
class RecommendSearchConditionItem(BaseModel):
    user_requirement: str = Field(
        ...,
        description="Directly quoted user requirement, e.g. '14-inch screen, portable, for Battlefield'.",
    )
    filter_condition: FilterConditions = Field(
        ...,
        description=(
            "Detailed laptop filters inferred from user requirements. "
            "Use string values; multiple values separated by '|', "
            "single values as string, ranges as 'min~max'."
        ),
    )


class RecommendSearchRequest(Request):
    """Product Recall input parameter"""

    product_search_conditions: List[RecommendSearchConditionItem] = Field(
        ..., description="List of user requirements and filter conditions"
    )
    recommend_size: Optional[int] = Field(
        description="Maximum number of items to return", default=15
    )
    up_down_status: Optional[bool] = Field(
        description="Whether to filter by up/down status", default=True
    )
    sort_by: Optional[str] = Field(
        description="Sorting order: 'price_asc' for price ascending, 'price_desc' for price descending, 'popularity' for balanced release time and popularity",
        default="popularity",
        enum=["price_asc", "price_desc", "popularity"],
        alias="tag_value",
    )


class RecommendSKUItem(SKUCardModel):
    match_requirements: List[Dict[str, Any]] = Field(
        ..., description="List of match requirements as key-value pairs"
    )


class RecommendSearchResponse(ToolResponse):
    """Product Recall output parameter"""

    metadata: Optional[Dict[str, Any]] = Field(
        description="Additional metadata for llm response", default=None
    )
    summary_constraints: Optional[Union[str, List[str]]] = Field(
        default=""
    )


# ============= Frontend Filter Request 相关数据模型 =============


class FrontendFilterConditions(BaseModel):
    """前端筛选条件模型，仅支持指定的字段类型"""

    # Cascade类型字段 - 数据类型: List[List[str]]
    brand: Optional[List[List[str]]] = Field(
        default=None,
        description="品牌级联选择器，格式3元素列表对应BrandCondition(brand/sub_brand/series),缺失项为空: [['lenovo','ThinkPad','E Series'], ['lenovo','ThinkPad','']]",
        examples=[[["lenovo", "ThinkPad", "E Series"], ["lenovo", "ThinkPad", ""]]],
    )
    cpu: Optional[List[List[str]]] = Field(
        default=None,
        description="CPU级联选择器（三级级联），格式: [['Intel', 'Intel Core', 'Intel Core i7']]",
        examples=[
            [
                ["Intel", "Intel Core", "Intel Core i7"],
                ["AMD", "AMD Ryzen", "AMD Ryzen 5"],
            ]
        ],
    )
    gpu: Optional[List[List[str]]] = Field(
        default=None,
        description="GPU级联选择器，格式: [['Dedicated Graphics', 'NVIDIA GeForce RTX', '4070']]",
        examples=[[["Dedicated Graphics", "NVIDIA GeForce RTX", "4070"]]],
    )
    operating_system: Optional[List[List[str]]] = Field(
        default=None,
        description="操作系统级联选择器，格式: [['Windows', '11 Pro']]",
        examples=[[["Windows", "11 Pro"], ["Mac OS", "15.0"]]],
    )

    # Enum类型字段 - 数据类型: List[str]
    screen_size: Optional[List[str]] = Field(
        default=None,
        description="屏幕尺寸枚举选择器，格式: ['13.0\"-13.9\"', '14.0\"-14.9\"']",
        examples=[['13.0"-13.9"', '14.0"-14.9"']],
    )
    storage: Optional[List[str]] = Field(
        default=None,
        description="存储枚举选择器，格式: ['512GB SSD', '1TB SSD']",
        examples=[["512GB SSD", "1TB SSD"]],
    )
    ram: Optional[List[str]] = Field(
        default=None,
        description="RAM枚举选择器，格式: ['8 GB', '16 GB']",
        examples=[["8 GB", "16 GB"]],
    )

    # Range类型字段 - 数据类型: Dict[str, float]
    price: Optional[Dict[str, float]] = Field(
        default=None,
        description="价格范围选择器，格式: {'min': 500.0, 'max': 1000.0}",
        examples=[{"min": 500.0, "max": 1000.0}],
    )
    weight: Optional[Dict[str, float]] = Field(
        default=None,
        description="重量范围选择器，格式: {'min': 1.0, 'max': 2.5}",
        examples=[{"min": 1.0, "max": 2.5}],
    )

    # 新增额外字段
    model: Optional[List[str]] = Field(
        default=None,
        description="产品型号，格式: ['Lenovo Yoga Slim 7 14ITL05', 'Lenovo ThinkPad P16 Gen 3']",
    )
    year: Optional[List[str]] = Field(
        default=None,
        description="发布年份，格式: ['2022', '2023']",
    )
    user_group: Optional[List[str]] = Field(
        default=None,
        description="用户群体，格式: ['gamers', 'creators']",
    )
    color: Optional[List[str]] = Field(
        default=None,
        description="颜色，格式: ['black', 'silver']",
    )

    class Config:
        extra = "allow"

    def model_dump(self, **kwargs):
        # 如果 exclude_none 没有在 kwargs 中指定，则设置为 True
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class FrontendFilterSearchRequest(BaseModel):
    """前端筛选搜索请求，使用前端格式的筛选条件"""

    model_config = {"populate_by_name": True}  # 允许同时使用字段名和别名

    filter_conditions: FrontendFilterConditions = Field(
        description="前端格式的筛选条件",
        default=None,
    )
    size: int = Field(
        description="Maximum number of items to return", default=200, min=10, max=200
    )
    page: int = Field(description="Page number (1-based)", default=1, min=1)
    content_match: Optional[bool] = Field(
        description="Whether to use content matching", default=False
    )
    enable_brand_diversity: Optional[bool] = Field(
        description="Whether to enable brand diversity reranking", default=False
    )
    up_down_status: Optional[bool] = Field(
        description="Whether to filter by up/down status", default=True
    )
    sort_by: Optional[str] = Field(
        description="Sorting order: 'price_asc' for price ascending, 'price_desc' for price descending, 'popularity' for balanced release time and popularity",
        default="popularity",
        enum=["price_asc", "price_desc", "popularity"],
        alias="tag_value",
    )
    uid: Optional[str] = Field(
        description="User ID for personalized features (wish list, compare list)",
        default=None,
    )


# ============= Query Search Request 相关数据模型 =============
class QuerySearchRequest(Request):

    model_config = {"populate_by_name": True}  # 允许同时使用字段名和别名
    filter_conditions: FilterConditions = Field(
        description="Specific filter conditions mentioned by the user. For example, CPU model, GPU model, ",
        default=None,
    )
    sort_by: Optional[str] = Field(
        description="Sorting order: 'price_asc' for price ascending, 'price_desc' for price descending, 'popularity' for balanced release time and popularity",
        default="popularity",
        enum=["price_asc", "price_desc", "popularity"],
        alias="tag_value",
    )


class QuerySearchResponse(ToolResponse):
    metadata: Optional[Dict[str, Any]] = Field(
        description="Additional metadata for llm response", default=None
    )
