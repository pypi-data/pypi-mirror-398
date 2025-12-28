#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
]

from typing import List, Optional

from pydantic import BaseModel, Field

from agent_types.common import Request


class KnowledgeConfig(BaseModel):
    table: str
    table_key: str = Field(default="paragraph_id")

    collection: str
    collection_fields: List[str] = Field(
        default_factory=lambda: ["paragraph_id", "paragraph", "source", "start_time", "expire_time", "keywords"]
    )
    collection_vectors: List[str] = Field(
        default_factory=lambda: ["paragraph", "query", "summary"]
    )
    collection_indices: List[str] = Field(
        default_factory=lambda: ["source"]
    )
    doc_field: str = Field(
        default="paragraph"
    )

    related_query_field: Optional[str] = Field(default="related_query")
    related_query_split_comma: Optional[str] = Field(default="||")
    source_field: Optional[str] = Field(default="source")

    start_time_field: Optional[str] = Field(default=None)
    expire_time_field: Optional[str] = Field(default=None)
    start_expire_check_interval: int = Field(default=3600)


class KnowledgeInitRequest(Request):
    __request_name__ = "knowledge_init"

    table: str = Field()
    collection: str = Field()
    config: Optional[KnowledgeConfig] = Field(default_factory=KnowledgeConfig)
    replace: bool = Field(
        default=True,
        description="是否重新建表, 如果已经存在, 则先删除后建表"
    )
    n_sample: int = Field(default=-1)
