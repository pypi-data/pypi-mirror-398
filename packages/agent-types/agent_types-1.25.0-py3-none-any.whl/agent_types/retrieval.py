#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
    "DenseEmbeddingRequest",
    "DenseEmbeddingResponse",
    "SparseEmbeddingRequest",
    "QueryEncodingRequest",
    "DocumentEncodingRequest",
    "SparseEmbeddingResponse",
    "RerankingRequest",
    "RerankingResponse",
    "RetrievalRequest",
    "RetrievalResponse",
    "InsertRequest",
    "InsertResponse",
    "DeleteRequest",
    "DeleteResponse",
    "CollectionExistsRequest",
    "CollectionExistsResponse",
    "CreateCollectionRequest",
    "CreateCollectionResponse",
    "DropCollectionRequest",
    "DropCollectionResponse",
]

from typing import Any, Dict, List, Optional, Union

from pydantic import ConfigDict, Field, model_validator

from agent_types.common import CSRArray, FieldSchema, NDArray, Request, Response


class DenseEmbeddingRequest(Request):
    """稠密向量表征请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "dense_encode"

    text: Union[str, List[str]] = Field(
        title="文本",
        description="需要表征的文本"
    )
    normalize: bool = Field(
        title="是否规一化",
        description="是否对结果向量进行规一化",
        default=True
    )


class DenseEmbeddingResponse(Response):
    """稠密向量表征响应"""

    model_config = ConfigDict(extra="allow")

    embedding: NDArray = Field(
        title="表征向量",
        description="稠密表征向量（若表征多条文本，则返回矩阵）"
    )


class SparseEmbeddingRequest(Request):
    """稀疏向量编码"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "sparse_encode"

    text: Union[str, List[str]] = Field(
        title="文本",
        description="需要表征的文本"
    )


class QueryEncodingRequest(SparseEmbeddingRequest):
    """面向Query的稀疏向量编码"""

    __request_name__ = "encode_queries"


class DocumentEncodingRequest(SparseEmbeddingRequest):
    """面向Document的稀疏向量编码"""

    __request_name__ = "encode_documents"


class SparseEmbeddingResponse(Response):
    """稀疏向量编码"""

    model_config = ConfigDict(extra="allow")

    embedding: CSRArray = Field(
        title="表征向量",
        description="稀疏表征向量（若表征多条文本，则返回矩阵）"
    )


class RerankingRequest(Request):
    """重排序请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "rerank"

    query: str = Field(
        title="用户查询",
        description="检索所需的用户查询"
    )
    documents: List[str] = Field(
        title="用户查询检索数据集",
        description="用户查询检索数据集(粗排结果)"
    )
    top_k: int = Field(
        title="重排序检索返回Top-k",
        description="重排序检索返回Top-k",
        default=6,
        ge=1,
        le=50
    )
    return_scores: bool = Field(
        title="是否返回分数",
        description="是否返回分数",
        default=True
    )
    return_documents: bool = Field(
        title="是否返回召回文档",
        description="是否返回召回文档",
        default=False
    )


class RerankingResponse(Response):
    """重排序响应"""

    model_config = ConfigDict(extra="allow")

    ranked: List[int] = Field(
        title="重排序检索返回Top-K索引",
        description="重排序检索返回Top-K索引",
        default_factory=list
    )
    scores: List[float] = Field(
        title="重排序检索返回Top-K分数",
        description="重排序检索返回Top-K索引",
        default_factory=list
    )
    documents: Optional[List[str]] = Field(
        title="召回文档",
        description="召回文档",
        default=None
    )


class RetrievalRequest(Request):
    """知识库检索请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "retrieval"

    collections: List[str] = Field(
        title="检索集合名称",
        description="检索集合名称，多个取值表示同时从多个集合中检索"
    )
    query: str = Field(
        title="用户查询",
        description="检索所需的用户查询"
    )
    top_k: int = Field(
        title="检索返回Top-k",
        description="检索返回Top-k",
        default=6,
        ge=1,
        le=50
    )
    expr: Dict[str, str] = Field(
        title="元数据表达式",
        description="元数据表达式，即筛选条件",
        default_factory=dict
    )
    index_fields: List[str] = Field(
        title="索引字段名称",
        description="索引字段的名称，默认为vector，可以指定多个表示混合检索",
        default_factory=lambda: ["vector"]
    )
    output_fields: Optional[List[str]] = Field(
        title="返回字段",
        description="检索结果中需包含的字段列表, 默认返回除向量字段以外的所有字段",
        default=None
    )
    use_rerank: bool = Field(
        title="是否使用Rerank",
        description="是否使用Rerank",
        default=True
    )
    rerank_url: Optional[str] = Field(
        title="Rerank服务的URL",
        description="Rerank服务的URL，该URL主要针对自定义rerank服务；这里如果不指定则使用检索服务启动时配置的rerank服务。",
        default=None
    )
    pre_top_k: Optional[int] = Field(
        title="Rerank候选集大小",
        description="Rerank候选集大小",
        default=None,
        ge=1,
        le=50
    )
    search_kw: Optional[Dict] = Field(
        title="可选检索参数",
        description="可选检索参数(`keywords`, `timeout`, ...)",
        default_factory=dict,
    )


class RetrievalResponse(Response):
    """知识库检索响应"""

    model_config = ConfigDict(extra="allow")

    distance: List[float] = Field(
        title="检索距离",
        description="检索距离",
        default_factory=list
    )
    scores: List[float] = Field(
        title="重排分数",
        description="重排分数",
        default_factory=list
    )
    items: List[Dict] = Field(
        title="检索对象列表",
        description="检索对象列表",
        default_factory=list
    )
    retrieval_info: Optional[Dict] = Field(
        title="Extra检索消息详情",
        description="Extra检索消息详情(`timing`, `processing`, ...)",
        default_factory=dict
    )


class InsertRequest(Request):
    """插入知识样本"""

    __request_name__ = "insert"

    collection: str = Field(
        title="表名",
        description="若表不存在则会自动执行创建，其表结构由插入的第一个样本的属性名称及类型推导而来"
    )
    documents: List[Dict] = Field(
        title="插入数据集",
        default_factory=list,
        max_length=1024
    )
    indexed_field: str = Field(
        title="数据集索引列[Key]",
        default="text"
    )
    indexed_related_field: Optional[str] = Field(
        title="数据集索引列[Value]",
        default=None,
    )

    @model_validator(mode="after")
    def _model_validator_value(self):
        self.indexed_related_field = self.indexed_related_field or self.indexed_field
        return self


class InsertResponse(Response):
    """插入知识样本"""

    insert_msg: str = Field(
        title="插入数据消息",
        default=""
    )
    insert_count: int = Field(
        title="插入数据集长度",
        default=-1
    )


class DeleteRequest(Request):
    """删除样本"""

    __request_name__ = "delete"

    collection: str = Field(
        title="Milvus Collection Name"
    )
    expr: Optional[str] = Field(
        title="基于元数据表达式删除",
        default=None
    )
    delete_primary_ids: List = Field(
        title="基于ID删除",
        default_factory=list
    )

    @model_validator(mode="after")
    def _model_validator_value(self):
        ids = self.delete_primary_ids
        if ids:
            e1 = f"_id in {ids}"  # TODO, fixed,
            expr = e1 if not self.expr else f"({self.expr}) or ({e1})"
            self.expr = expr
        return self


class DeleteResponse(Response):
    """删除样本"""

    delete_count: int = Field(
        title="删除数据集长度",
        default=-1
    )


class CollectionExistsRequest(Request):
    """判断知识集合是否存在"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "collection_exists"

    collection: str = Field(
        title="集合名称",
        description="集合（表）名称"
    )


class CollectionExistsResponse(Response):
    """判断知识集合是否存在"""

    model_config = ConfigDict(extra="allow")

    exists: bool = Field(
        title="是否存在",
        description="知识集合是否已存在"
    )


class CreateCollectionRequest(Request):
    """创建知识库集合（表）"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "create_collection"

    collection: str = Field(
        title="集合名称",
        description="集合（表）名称，必须是当前数据库中不存在的表名"
    )
    reference_document: Optional[Dict[str, Any]] = Field(
        title="参考文档",
        description=(
            "如果给定参考文档，系统则根据参考文档中的各属性推断要创建的集合的列名及其数据类型。"
            "推断的类型一般具有普适性，但可能在性能上不是最优的，因此要指定相关细节请使用collection_schema列表。"
        )
    )
    collection_schema: List[FieldSchema] = Field(
        title="集合模式描述列表",
        description=(
            "如果通过参考文档不足以表达要创建的集合的列属性，则可通过schema列表指定。"
            "通过这种方式能更细致的描述集合，但配置起来也更复杂。"
        )
    )
    insert_ref_doc: bool = Field(
        title="适合否插入参考文档",
        description="创建集合后，是否将参考文档插入新集合中",
        default=False
    )
    sparse_encoding_url: Optional[str] = Field(
        title="稀疏编码服务URL",
        description="稀疏编码服务URL，为空表示使用该检索服务的默认稀疏编码。",
        default=None
    )
    dense_encoding_url: Optional[str] = Field(
        title="稠密编码服务URL",
        description="稠密编码服务URL，为空表示使用该检索服务的默认稠密编码。",
        default=None
    )


class CreateCollectionResponse(Response):
    """创建知识库集合（表）"""

    model_config = ConfigDict(extra="allow")

    success: bool = Field(
        default=True,
        title="建表是否成功",
        description="建表是否成功"
    )


class DropCollectionRequest(Request):
    """删除知识库集合（表）"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "drop_collection"

    collection: str = Field(
        title="集合名称",
        description="集合（表）名称，必须是当前数据库中已存在的表名"
    )
    auth_key: Optional[str] = Field(
        title="安全校验口令",
        description=(
            "删除集合属于危险操作，建议搭配安全检验口令。"
            "这个口令可以是在服务启动的时候由管理员设置的，在服务实现删除操作的逻辑中，增加安全口令的验证。"
            "当然，如果不怕危险也可以忽略这个参数。"
        ),
        default=None
    )


class DropCollectionResponse(Response):
    """删除知识库集合（表）"""

    model_config = ConfigDict(extra="allow")

    delete_count: int = Field(
        title="删除数据集长度",
        description="删除数据集长度",
        default=-1
    )
