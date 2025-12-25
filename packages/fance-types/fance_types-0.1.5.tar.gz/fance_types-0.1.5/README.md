# fance_types模块

## 数据结构定义

fance_types/common.py

主要定义系统中的通用数据结构，包括数据处理、算法、后端等需要在模块间共享的数据结构。

定义为pydantic.BaseModel的子类。

## 接口定义

接口定义按照其业务逻辑写在对应名字的文件中，例如推荐逻辑的接口，可以写在fance_types/recommend.py中。

接口主要包含3部分：接口名称、输入和输出。可以通过两个数据结构来定义，分别为：请求对象（Request）和响应对象（Response）。其中接口名称可以包含在请求对象中。例如：

```python
GetInfoRequest(Request):
    """相关注释说明"""
    
    # 如果继承自agent_types.common.Request基类，那么可以设置一个请求名称，相当于该接口的名称
    # 具体用法请参考agentcortex仓库中的examples
    __request_name__ = "get_info"
    
    field1: Optional[str] = Field(
        title="该字段的标题",
        description="该字段的描述（给人看的，也可以给LLM看）",
        default=None  # "默认值（如有）"
    )
    field2: List[int] = Field(
        title="该字段的标题",
        description="该字段的描述（给人看的，也可以给LLM看）",
        default_factory=list  # 默认值也可以是工厂函数
    )
    ......
```

Response类的定义类似。
