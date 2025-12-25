#!/usr/bin/env python3

__author__ = "xi"

from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class CPU(BaseModel):
    """CPU"""

    id: str = Field(
        title="CPU标识",
        description="CPU的唯一标识符"
    )
    vendor: str = Field(
        title="发行厂商",
        description="CPU的制造或发行厂商，如Intel、AMD"
    )
    processor_branding: str = Field(
        title="品牌名",
        description="CPU品牌名，如Core i7、Ryzen 7"
    )
    model: str = Field(
        title="型号",
        description="CPU型号，如11600K、4930MX"
    )
    processor_type: str = Field(
        title="CPU类型",
        description="CPU类型，如Desktop（桌面版）、Mobile（移动版）"
    )
    series: str = Field(
        title="系列名",
        description="CPU所属的系列，如Core、Pentium、Ryzen"
    )
    cores: int | None = Field(
        title="核心数",
        description="核心数",
        default=None
    )
    threads: int | None = Field(
        title="线程数",
        description="线程数",
        default=None
    )
    cache: str | None = Field(
        title="缓存",
        description="缓存",
        default=None
    )
    release_year: int | None = Field(
        title="发布年份",
        description="CPU的发布年份",
        default=None
    )
    multi_thread_score: float | None = Field(
        title="测评多核得分",
        description="CPU的性能测评多核得分，可能为空",
        default=0
    )
    single_thread_score: float | None = Field(
        title="测评单核得分",
        description="CPU的性能测评单核得分，可能为空",
        default=0
    )


class GPU(BaseModel):
    """GPU"""

    gpu_id: str = Field(
        title="GPU标识",
        description="GPU的唯一标识符"
    )
    vendor: str = Field(
        title="发行厂商",
        description="GPU的制造或发行厂商，如NVIDIA、AMD",
        default=""
    )
    model: str = Field(
        title="型号",
        description="GPU型号",
        default=""
    )
    series: str | None = Field(
        title="系列",
        description="GPU系列",
        default=""
    )
    type: str = Field(
        title="显卡类型",
        description="显卡类型，例如独立显卡、核心显卡"
    )
    memory_size: str | None = Field(
        title="显存容量",
        description="显存容量", default=None
    )
    vram_type: str | None = Field(
        title="显存类型",
        description="显存类型，如DDR4、DDR5或`Shared Memory`",
        default=None,
        json_schema_extra={"raw": "architecture"},
    )
    score: float | None = Field(
        title="测评得分",
        description="GPU的性能测评得分，可能为空",
        default=0
    )


class ProductProfile(BaseModel):
    """商品画像"""

    product_id: str = Field(
        title="商品ID",
        description="商品唯一标识符"
    )
    sku_id: str = Field(
        title="SKU ID",
        description="商品对应SKU标识符",
        json_schema_extra={"raw": "sku"},
    )
    spu_id: str = Field(
        title="SPU ID",
        description="商品对应SPU标识符"
    )

    product_name: str = Field(
        title="商品名称",
        description="商品名称",
        json_schema_extra={"raw": "product_title"},
    )
    product_url: str = Field(
        title="商品URL",
        description="商品URL"
    )
    shop_name: str = Field(
        title="店铺名称",
        description="店铺名称"
    )
    official_store: int = Field(
        title="店铺来源",
        description="是否官方：1表示官网，2表示Amazon直营，3表示其他店铺",
        json_schema_extra={"raw": "is_official_store"},
    )
    up_down_status: bool = Field(
        title="上架状态",
        description="商品上下架状态，1:上架；2:下架"
    )
    current_price: float | None = Field(
        title="当前价格",
        description="商品当前售价"
    )
    origin_price: float | None = Field(
        title="原价",
        description="商品原始售价",
        default=None
    )
    bought_in_past_month: int | None = Field(
        title="月销量",
        description="估计一个月内销量",
        default=0
    )
    delivery: str | None = Field(
        title="配送信息",
        description="配送信息，如是否包邮",
        default=None
    )
    return_policy: str | None = Field(
        title="退换货政策",
        description="退换货政策说明",
        default=None
    )

    @model_validator(mode="after")
    def _custom_validate(self):
        if self.up_down_status:
            if not (self.current_price is not None and self.origin_price is not None):
                raise ValueError(
                    f"`current_price` and `original_price` should not be `None` "
                    f"when `up_down_status` is `True`."
                )
        return self


class Product(ProductProfile):
    """商品视图"""

    reviews_count: int = Field(
        title="评论数",
        description="商品评论总数",
        default=0
    )
    reviews_star_distribution: dict = Field(
        title="评论星级分布",
        description="商品评论的星级分布情况",
        default_factory=dict
    )
    reviews_rating: float | None = Field(
        title="平均评分",
        description="商品评论平均得分",
        default=None
    )
    warranty: str | None = Field(
        title="保修政策",
        description="商品保修政策",
        default=None
    )


class SPUProfile(BaseModel):
    """SPU画像"""

    spu_id: str = Field(
        title="SPU ID",
        description="商品对应SPU标识符"
    )
    spu_name: str = Field(
        title="SPU名称",
        description="商品对应的SPU名称"
    )
    category: str = Field(
        title="类别",
        description="商品类别"
    )
    brand: str = Field(
        title="品牌",
        description="商品对应的品牌"
    )
    sub_brand: str = Field(
        title="子品牌",
        description="品牌的下属子品牌"
    )
    series: str = Field(
        title="系列",
        description="产品所属系列",
    )
    model: str = Field(
        title="型号",
        description="产品型号"
    )

    spu_category: str | None = Field(
        title="类别",
        description="商品类别",
        default=None
    )
    user_group: list[str] | str | None = Field(
        title="用户群体",
        description="针对商品的用户群体",
        default=None
    )
    one_sentence_summary: str | None = Field(
        title="一句话概述",
        description="对商品的简短总结",
        default=None
    )
    pros: str | None = Field(
        title="优点",
        description="商品优点或卖点",
        default=None
    )
    cons: str | None = Field(
        title="缺点",
        description="商品缺点或不足",
        default=None
    )
    target_market: str | None = Field(
        title="目标市场",
        description="商品目标消费群体",
        default=None
    )


class SKUConfig(BaseModel):
    """SKU配置"""

    sku_id: str

    cpu: str | None = ""
    gpu: str | None = ""
    ram: int | None = None
    storage: str | None = ""
    screen: str | None = ""
    color: str | None = ""
    system: str | None = ""


class SPU(SPUProfile):
    """SPU视图"""

    reviews_count: int = Field(
        title="评论数",
        description="商品评论总数",
        default=0
    )
    reviews_star_distribution: dict = Field(
        title="评论星级分布",
        description="商品评论的星级分布情况",
        default_factory=dict
    )
    reviews_rating: float | None = Field(
        title="平均评分",
        description="商品评论平均得分",
        default=None
    )

    config_list: list[SKUConfig] = Field(
        title="配置列表",
        description="该SPU所包含的SKU配置列表",
        default_factory=list
    )

    up_down_status: bool = Field(
        title="上架状态",
        description="商品上下架状态",
        default=False
    )
    top_labels: str | None = Field(
        title="商品标签",
        description="商品的热门标签",
        default=None
    )

    num_product: int = Field(
        title="商品数量",
        description="该SPU所包含的所有商品数量",
        default=0
    )

    def get_switches(self) -> dict[str, list[str | int]]:
        switches: dict[str, set] = {}

        for config in self.config_list:
            for name in config.model_fields.keys():
                if name == "sku_id":
                    continue
                value = getattr(config, name)

                if name not in switches:
                    switches[name] = set()

                switches[name].add(value)

        result = {
            name: list(switch_set)
            for name, switch_set in switches.items()
        }

        for switch_list in result.values():
            switch_list.sort()

        return result


class Picture(BaseModel):
    """商品图片"""

    image_id: str = Field(
        title="图片ID",
        description="图片唯一标识符"
    )
    thumbnail_s3_url: str | None = Field(
        title="缩略图URL",
        description="图片缩略图的S3链接",
        default=None
    )
    carousel_s3_url: str | None = Field(
        title="轮播图URL",
        description="图片轮播图的S3链接",
        default=None
    )
    original_image_thumbnail_s3_url: str | None = Field(
        title="原图缩略图URL",
        description="原图的缩略图S3链接",
        default=None
    )
    original_image_carousel_s3_url: str | None = Field(
        title="原图轮播图URL",
        description="原图的轮播图S3链接",
        default=None
    )
    flag: int = Field(
        title="标记",
        description="为0标识使用原始URL",
        default=0
    )


class SKUProfile(BaseModel):
    """SKU画像"""

    sku_id: str = Field(
        title="SKU ID",
        description="商品对应SKU标识符",
        json_schema_extra={"raw": "sku"},
    )
    spu_id: str = Field(
        title="SPU ID",
        description="商品对应SPU标识符",
    )
    spu_name: str = Field(
        title="SPU名称",
        description="商品对应SPU名称",
    )
    brand: str = Field(
        title="品牌",
        description="商品品牌",
    )
    sub_brand: str = Field(
        title="子品牌",
        description="品牌的下属子品牌",
    )
    series: str = Field(
        title="系列",
        description="产品系列",
    )
    model: str = Field(
        title="型号",
        description="产品型号",
    )

    cpu_id: str = Field(
        title="CPU ID",
        description="CPU标识符",
    )
    gpu_id: str | None = Field(
        title="GPU ID",
        description="GPU标识符",
        default=None,
    )
    graphics_card_type: str = Field(
        title="显卡类型",
        description="GPU类型或类别",
    )

    ram_size: int = Field(
        title="内存容量",
        description="内存大小，单位GB",
    )
    ram_type: str | None = Field(
        title="内存类型",
        description="内存类型，如DDR4",
        default=None,
    )
    ram_configuration: str | None = Field(
        title="内存配置",
        description="内存插槽配置，如8GBx2",
        default=None,
    )
    ram_speed: str | None = Field(
        title="内存频率",
        description="内存工作频率，如3200MHz",
        default=None,
    )

    storage_size: int = Field(
        title="存储容量",
        description="总存储容量，单位GB",
    )
    storage_type: str = Field(
        title="存储类型",
        description="存储类型，如SSD、HDD",
    )
    storage_ssd_size: int | None = Field(
        title="SSD容量",
        description="SSD存储容量，单位GB",
        default=None,
    )
    storage_hdd_size: int | None = Field(
        title="HDD容量",
        description="HDD存储容量，单位GB",
        default=None,
    )

    screen_size: float = Field(
        title="屏幕尺寸",
        description="屏幕对角线尺寸，单位英寸",
    )
    screen_resolution: str | None = Field(
        title="屏幕分辨率",
        description="屏幕分辨率，如1920x1080",
        default=None,
    )
    screen_aspect_ratio: str | None = Field(
        title="屏幕长宽比",
        description="屏幕宽高比，如16:9",
        default=None,
        json_schema_extra={"raw": "aspect_ratio"},
    )
    screen_refresh_rate: str | None = Field(
        title="刷新率",
        description="屏幕刷新率，如60Hz、120Hz",
        default=None,
    )
    screen_brightness: str | None = Field(
        title="屏幕亮度",
        description="屏幕亮度，如300nit",
        default=None,
    )
    screen_color_gamut: str | None = Field(
        title="色域",
        description="屏幕覆盖的色域，如sRGB、AdobeRGB",
        default=None,
    )
    screen_anti_glare: bool | None = Field(
        title="防眩光",
        description="屏幕是否有防眩光处理",
        default=None,
    )
    screen_panel_type: str | None = Field(
        title="屏幕面板类型",
        description="屏幕面板类型，如IPS、TN",
        default=None,
        json_schema_extra={"raw": "panel_type"},
    )
    screen_ppi: int | None = Field(
        title="屏幕像素密度",
        description="屏幕像素密度，单位PPI",
        default=None,
    )
    screen_touch_type: str | None = Field(
        title="触控类型",
        description="屏幕触控类型，如多点触控",
        default=None,
    )
    screen_is_touch: bool | None = Field(
        title="是否是触屏",
        description="是否是触屏",
        default=None,
        json_schema_extra={"raw": "touchscreen"},
    )

    color: str = Field(
        title="颜色",
        description="商品颜色",
    )
    item_dimensions: str | None = Field(
        title="尺寸",
        description="商品外观尺寸",
        default=None,
    )
    weight: float | None = Field(
        title="重量",
        description="商品重量，单位千克",
        default=None,
    )

    numeric_keypad: bool | None = Field(
        title="数字小键盘",
        description="是否配备数字小键盘",
        default=None,
    )
    keyboard_backlit: bool | None = Field(
        title="键盘背光",
        description="键盘是否有背光",
        default=None,
    )
    trackpad: str | None = Field(
        title="触控板",
        description="触控板类型或说明",
        default=None,
    )
    fingerprint_reader: bool | None = Field(
        title="指纹识别",
        description="是否支持指纹识别",
        default=None,
    )
    rear_webcam_resolution: str | None = Field(
        title="后置摄像头",
        description="后置摄像头像素或分辨率",
        default=None,
    )
    hdmi: int | None = Field(
        title="HDMI接口",
        description="HDMI接口数量",
        default=None,
    )
    port_usb3_0: int | None = Field(
        title="USB 3.0接口",
        description="USB 3.0接口数量",
        default=None,
    )
    port_usb2_0: int | None = Field(
        title="USB 2.0接口",
        description="USB 2.0接口数量",
        default=None,
    )
    internet_ethernet: int | None = Field(
        title="以太网接口",
        description="以太网接口数量",
        default=None,
    )
    wifi_gen: str | None = Field(
        title="WiFi标准",
        description="无线网卡标准，如WiFi6",
        default=None,
    )
    bluetooth: str | None = Field(
        title="蓝牙",
        description="是否支持蓝牙",
        default=None,
    )

    battery: str | None = Field(
        title="电池",
        description="电池类型",
        default=None,
    )
    battery_capacity: str | None = Field(
        title="电池容量",
        description="电池容量，如50Wh",
        default=None,
    )
    battery_rated_life: str | None = Field(
        title="续航时间",
        description="电池额定续航时间",
        default=None,
        json_schema_extra={"raw": "rated_battery_life"},
    )
    power_adapter: str | None = Field(
        title="电源适配器",
        description="电源适配器规格",
        default=None,
    )

    os_family: str = Field(
        title="操作系统家族",
        description="操作系统类别，如Windows、Linux",
    )
    os_model: str | None = Field(
        title="操作系统版本",
        description="操作系统具体版本，如Windows 11",
        default=None,
    )

    warranty: str | None = Field(
        title="保修",
        description="商品保修政策",
        default=None,
    )
    year: str | None = Field(
        title="年份",
        description="商品年份",
        default=None,
    )
    spu_year: str | None = Field(
        title="SPU年份",
        description="SPU对应的年份",
        default=None,
    )

    @model_validator(mode="after")
    def _custom_validate(self):
        if self.graphics_card_type.lower() != "integrated" and self.gpu_id is None:
            raise ValueError(
                f"`gpu_id` should not be `None` "
                f"when `graphics_card_type` is `Integrated`."
            )
        return self


class SKU(SKUProfile):
    """SKU视图"""

    weight_lb: float | None = Field(
        title="重量",
        description="商品重量，单位磅",
        default=None,
    )

    cpu: CPU | None = Field(
        title="CPU信息",
        description="SKU对应的CPU对象",
        default=None,
    )
    gpu: GPU | None = Field(
        title="GPU信息",
        description="SKU对应的GPU对象",
        default=None,
    )

    max_price: float | None = Field(
        title="最高价",
        description="SKU最高售价",
        default=None,
    )
    min_price: float | None = Field(
        title="最低价",
        description="SKU最低售价",
        default=None,
    )
    coupon_labels: bool = Field(
        title="优惠标签",
        description="是否有优惠券标签",
        default=False,
    )
    up_down_status: bool = Field(
        title="上架状态",
        description="SKU上下架状态",
        default=False,
    )

    bought_in_past_month: int = Field(
        title="月销量",
        description="估计一个月内销量",
        default=0,
    )
    reviews_star_distribution: dict = Field(
        title="评论星级分布",
        description="SKU评论星级分布",
        default_factory=dict,
    )
    reviews_rating: float | None = Field(
        title="平均评分",
        description="SKU评论平均评分",
        default=None,
    )
    reviews_count: int = Field(
        title="评论数量",
        description="SKU评论数量",
        default=0,
    )

    thumbnail_s3_urls: list[str] = Field(
        title="缩略图列表",
        description="SKU缩略图URL列表",
        default_factory=list,
    )
    carousel_s3_urls: list[str] = Field(
        title="轮播图列表",
        description="SKU轮播图URL列表",
        default_factory=list,
    )

    num_product: int = Field(
        title="商品数量",
        description="该SKU对应商品数量",
        default=0,
    )

    def model_post_init(self, context: Any, /) -> None:
        if self.weight is not None:
            self.weight_lb = self.weight * 2.2


class SKUCard(BaseModel):
    """SKU卡片"""

    sku_id: str = Field(
        description="SKU ID",
    )
    image_url: str | None = Field(
        description="Image URL",
        default=None,
    )
    spu_name: str | None = Field(
        description="SPU Name",
        default=None,
    )
    attributes: str | None = Field(
        description="Attributes",
        default=None,
    )
    price: str | None = Field(
        description="Price",
        default=None,
    )
    discounts: str | None = Field(
        description="Current discounts",
        default=None,
    )
    pk: int | None = Field(
        description="Is in user's compare list",
        default=None,
    )
    wish: int | None = Field(
        description="Is in user's wish list",
        default=None,
    )


class ArticleCard(BaseModel):
    """文章卡片"""

    article_id: str = Field(
        description="Article ID",
    )
    title: str | None = Field(
        description="Article title",
        default=None,
    )
    content: str | None = Field(
        description="Article content",
        default=None,
    )
    img: str | None = Field(
        description="Article image URL",
        default=None,
    )
    author: str | None = Field(
        description="Article author",
        default=None,
    )
    time: str | None = Field(
        description="Article publish time",
        default=None,
    )
    link: str | None = Field(
        description="Article link",
        default=None,
    )
    summary_para1: str | None = Field(
        description="Summary paragraph 1",
        default=None,
    )
    summary_para2: str | None = Field(
        description="Summary paragraph 2",
        default=None,
    )
    summary_para3: str | None = Field(
        description="Summary paragraph 3",
        default=None,
    )
    svg: str | None = Field(
        description="SVG content",
        default=None,
    )
    tags: str | None = Field(
        description="Article tags",
        default=None,
    )
    thumbnail_image: str | None = Field(
        description="Thumbnail image URL",
        default=None,
    )
    source: str | None = Field(
        description="Article source",
        default=None,
    )
    published_date: str | None = Field(
        description="Published date",
        default=None,
    )
    published_date_normal: str | None = Field(
        description="Normalized published date",
        default=None,
    )
    labels: list[str] | None = Field(
        description="Article labels",
        default=None,
    )


class Citation(BaseModel):
    """引用"""

    model_config = ConfigDict(extra="allow")

    id: str | int = Field(
        description="引用ID",
    )
    title: str | None = Field(
        None,
        description="标题",
    )
    author: str | None = Field(
        None,
        description="作者",
    )
    published_date: str | None = Field(
        None,
        description="发布时间",
    )
    url: str | None = Field(
        None,
        description="链接",
    )
    image: str | None = Field(
        None,
        description="图片链接",
    )
    snippet: str | None = Field(
        None,
        description="摘要片段",
    )
    favicon: str | None = Field(
        description="Favicon URL of the source site",
        default=None,
    )
    domain: str | None = Field(
        description="Domain name of the source site",
        default=None,
    )


ToolType = Literal[
    "product_knowledge_search",
    "domain_general_knowledge_search",
    "compare_knowledge_retrieval",
    "web_search",
    "query_search",
    "recommend_search"
]
