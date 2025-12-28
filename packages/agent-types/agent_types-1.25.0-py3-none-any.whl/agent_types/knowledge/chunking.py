#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
    "TextChunkingRequest",
    "TextChunkingResponse",
    "TextChunkingBySentenceRequest",
    "TextChunkingByParagraphRequest",
    "TextChunkingByTokenRequest",
    "TextChunkingByLLMRequest",
    "TextChunkingByDelimiterRequest",
    "TextChunkingByMarkdownRequest",
    "TextChunkingBySemanticRequest",
    "TextChunkingByHybridRequest",
    "TextChunkingByRecursiveRequest",
]

from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from agent_types.common import Request, Response


class TextChunkingRequest(Request):
    """知识文本切分"""

    __request_name__ = "chunk_text"

    text: str = Field(
        title="要切分的文本",
        description="一般是文档解析后返回的内容。"
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
    max_size: int = Field(
        title="切片最大长度",
        description="切片对大长度",
        default=256
    )
    overlap: int = Field(
        title="相邻切片之间重叠字数",
        description="相邻切片之间重叠字数",
        default=50
    )


class TextChunkingResponse(Response):
    """知识文本切分"""

    chunks: List[str] = Field(
        title="分片列表",
        description="分片结果列表",
        default_factory=list
    )
    extra_info: Optional[Dict[str, Any]] = Field(
        title="额外信息",
        description="额外的信息,例如切片后可以返回切片在原文的位置信息",
        default=None
    )


class TextChunkingBySentenceRequest(TextChunkingRequest):
    """基于句子的切分"""

    __request_name__ = "chunk_text_by_sentence"


class TextChunkingByParagraphRequest(TextChunkingRequest):
    """基于段落的切分"""

    __request_name__ = "chunk_text_by_paragraph"


class TextChunkingByTokenRequest(TextChunkingRequest):
    """基于词元的切分"""

    __request_name__ = "chunk_text_by_token"


class TextChunkingByLLMRequest(TextChunkingRequest):
    """基于大模型的切分"""

    __request_name__ = "chunk_text_by_llm"

    custom_rules: Optional[str] = Field(
        title="用户自定义切分规则",
        description="用户使用自然语言描述的切分规则，将用作大模型提示词的一部分。",
        default=None
    )


class TextChunkingByDelimiterRequest(TextChunkingRequest):
    """基于分隔符的切分"""

    __request_name__ = "chunk_text_by_delimiter"

    delimiter: Optional[Union[str, List[str]]] = Field(
        title="",
        description="",
        default=[",", ".", "，", "。"]
    )


class TextChunkingByMarkdownRequest(TextChunkingRequest):
    """基于markdown结构的切分"""

    __request_name__ = "chunk_text_by_markdown"


class TextChunkingBySemanticRequest(TextChunkingRequest):
    """基于语义的切分"""

    __request_name__ = "chunk_text_by_semantic"


class TextChunkingByHybridRequest(TextChunkingRequest):
    """基于混合策略的切分"""

    __request_name__ = "chunk_text_by_hybrid"

    hybrid_strategy: Optional[List[str]] = Field(
        title="混合策略",
        description="混合策略列表, 例如 ['markdown', 'llm']",
        default_factory=lambda: ["markdown", "llm"]
    )


class TextChunkingByRecursiveRequest(TextChunkingRequest):
    """基于递归的切分"""

    __request_name__ = "chunk_text_by_recursive"
