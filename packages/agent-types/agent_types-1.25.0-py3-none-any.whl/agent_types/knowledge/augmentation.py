#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
    "TextAugmentationRequest",
    "TextAugmentationResponse",
    "TextAugmentationAsQueryRequest",
    "TextAugmentationAsQueryResponse",
    "TextAugmentationAsSummaryRequest",
    "TextAugmentationAsSummaryResponse",
    "TextAugmentationAsKeywordsRequest",
    "TextAugmentationAsKeywordsResponse",
    "TextAugmentationSubmissionRequest",
    "TextAugmentationSubmissionResponse",
]

from typing import Dict, Optional

from pydantic import Field

from agent_types.common import GenerationOptions, Request, Response, TaskSubmissionResponse


class TextAugmentationRequest(Request):
    """知识文本增强"""

    __request_name__ = "augment_text"

    text: str = Field(
        title="要增强的文本",
        description="一般是文档切块后返回的内容。"
    )
    text_type: str = Field(
        title="文本内容类型",
        description="文本内容类型, 例如：`md`, `txt`, `json`",
        default="md"
    )
    metadata: Optional[Dict] = Field(
        title="文档对应的metadata",
        description="文档对应的metadata",
        default_factory=dict
    )
    custom_rules: Optional[str] = Field(
        title="用户自定义增强规则",
        description="用户使用自然语言描述的增强规则，将用作大模型提示词的一部分。",
        default=None
    )


class TextAugmentationResponse(Response):
    """知识文本增强"""

    result: str = Field(
        title="文本增强结果",
        description="文本增强结果"
    )


class TextAugmentationAsQueryRequest(TextAugmentationRequest):
    """增强为相关查询（反向变换）"""

    __request_name__ = "augment_text_as_query"


class TextAugmentationAsQueryResponse(Response):
    """增强为相关查询"""

    result: str = Field(
        title="文本增强结果",
        description="文本增强结果"
    )


class TextAugmentationAsSummaryRequest(TextAugmentationRequest):
    """增强为总结"""

    __request_name__ = "augment_text_as_summary"


class TextAugmentationAsSummaryResponse(Response):
    """增强为总结"""

    result: str = Field(
        title="文本增强结果",
        description="文本增强结果"
    )


class TextAugmentationAsKeywordsRequest(TextAugmentationRequest):
    """增强为关键字"""

    __request_name__ = "augment_text_as_keywords"


class TextAugmentationAsKeywordsResponse(Response):
    """增强为关键字"""

    result: str = Field(
        title="文本增强结果",
        description="文本增强结果"
    )


class TextAugmentationSubmissionRequest(Request):
    """提交文本知识增强任务"""

    __request_name__ = "submit_text_augmentation"

    input_url: str = Field(
        title="输入数据URL",
        description="输入数据所在的数据库表URL，例如：mongodb://address/db/collection、mysql://address/db/table"
    )
    output_url: str = Field(
        title="输出数据URL",
        description="增强结果保存的数据库表URL，例如：mongodb://address/db/collection、mysql://address/db/table"
    )
    text_field: str = Field(
        title="文本字段",
        description="输入数据中存放文本内容的字段名称",
        default="paragraph"
    )
    text_type: str = Field(
        title="文本内容类型",
        description="输入文本的类型，例如：`md`（Markdown）、`txt`（纯文本）、`json`（JSON文档）",
        default="md"
    )
    output_query_field: Optional[str] = Field(
        title="增强为查询的输出字段",
        description="生成与该知识相关的查询，并写入到结果中的该字段。如果为None表示不进行该项增强",
        default="related_query"
    )
    output_summary_field: Optional[str] = Field(
        title="增强为总结的输出字段",
        description="生成该知识的总结内容，并写入到结果中的该字段。如果为None表示不进行该项增强",
        default="summary"
    )
    output_keywords_field: Optional[str] = Field(
        title="增强为关键字的输出字段",
        description="生成该知识相关的关键字，并写入到结果中的该字段。如果为None表示不进行该项增强",
        default=None
    )
    llm_name: Optional[str] = Field(
        title="大模型名称",
        description="用于执行增强任务的语言模型名称；如果为None，则使用系统默认模型",
        default=None
    )
    generation_options: Optional[GenerationOptions] = Field(
        title="生成配置项",
        description="用于控制大模型生成行为的参数设置，例如温度、top_p等；如果为None则使用默认配置",
        default=None
    )
    custom_rules: Optional[str] = Field(
        title="用户自定义增强规则",
        description="由用户使用自然语言描述的增强规则，这些规则会作为提示词的一部分传递给大模型",
        default=None
    )


class TextAugmentationSubmissionResponse(TaskSubmissionResponse):
    pass
