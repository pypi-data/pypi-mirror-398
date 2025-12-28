#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
    "Request",
    "Response",
    "Ref",
    "ToolResponse",
    "SystemProfile",
    "FewShot",
    "BasicKnowledge",
    "ToolKnowledge",
    "DecompositionKnowledge",
    "DomainKnowledge",
    "SystemMemory",
    "UserMemory",
    "ChatMessage",
    "Mention",
    "SessionMemory",
    "NDArray",
    "CSRArray",
    "FieldSchema",
    "Property",
    "Tool",
    "Intent",
    "ToolCalling",
    "Plan",
    "ExecutionError",
    "ExecutionStatus",
    "Observation",
    "LLMConfig",
    "GenerationOptions",
    "MCPServerConfig",
    "TaskSubmissionRequest",
    "TaskSubmissionResponse",
    "TaskStatusRequest",
    "TaskStatusResponse",
    "TaskCancelingRequest",
    "TaskCancelingResponse",
]

import base64
import io
import json
import re
from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic_core import ValidationError
from scipy.sparse import csr_array


class Request(BaseModel):
    """请求对象的基类
    所有接口的输入都继承自这个类

    以Request对象作为输入、以Response作为输出的函数称之为API函数。
    一个请求对象相当于一个API函数的入参的集合，即将函数所需要的的各个参数定义在了一个BaseModel对象中。
    这样做的优势包括：
    （1）能够以统一的形式调用所有的API函数。
    （2）BaseModel能够对函数执行前对各个参数进行类型检查，这对于系统的调试、维护，以及智能体的工具执行尤为重要。
    （3）便于自动生成API的接口描述信息，从而支持模块的即插即用特性。

    具体来讲，一个API函数通常定义为如下形式：

    def do_somthing(request: XxxRequest) -> XxxResponse:
        pass

    其中XxxRequest和XxxResponse定义为：

    class XxxRequest(Request):
        attribute1
        attribute2
        ...

    class XxxResponse(Response):
        attribute1
        attribute2
        ...
    """

    model_config = ConfigDict(extra="allow")

    trace_id: Optional[str] = Field(
        title="该次请求的标识符",
        description=(
            "主要用于跟踪该次请求的执行路径，一般作为该次请求执行过程中涉及到的所有日志信息的标识。"
            "如果在创建请求对象的时候不指定该属性，则为空。"
        ),
        default=None
    )

    __request_name__ = None  # 这个字段用于定义请求的名称
    __description__ = None  # 这个字段用于定义请求的描述信息

    @classmethod
    def get_request_path(cls) -> str:
        name = cls.__request_name__
        if name:
            if name.startswith("/"):
                return name
            else:
                return "/" + name
        else:
            name = cls.__name__
            if name.endswith("Request"):
                name = name[:-7]
            return "/" + cls._camel_to_snake(name)

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()


class Response(BaseModel):
    """响应对象的基类
    所有接口的输出都继承自这个类

    Response通常与Request成对定义，并同时使用。
    一个API函数可以返回一个或者多个Response对象，分别对应这个函数的“一次性输出模式”和“流式输出模式”。
    一次性输出模式和普通函数无异，流式输出模式通常有两种定义方式：
    （1）将函数定义为对应Response类型的生成器，例如：
        def do_something(request: XxxRequest) -> Iterable[XxxResponse]:
            ...
            yield XxxResponse()
            ...

    （2）函数仍然定义为普通函数，但其返回值是一个Response对象的生成器：
        def do_something(request: XxxRequest) -> Iterable[XxxResponse]:
            return (
                XxxResponse()
                for i in some_iterable
            )
    """

    model_config = ConfigDict(extra="allow")

    trace_id: Optional[str] = Field(
        title="被响应请求的标识符",
        description=(
            "该属性是对应请求对象中的trace_id属性。"
            "在构建响应对象时如果没有给出，一般也不自动生成，因为自动生成的ID无法和被响应请求的ID匹配，所以没有意义。"
        ),
        default=None
    )


class Ref(BaseModel):
    """可引用对象
    在结构化信息（尤其是工具输出）中，用来包装一个结构化数据对象，以引导LLM在规划、总结时能够直接进行引用。
    """

    value: Any = Field(
        title="值",
        description="可引用对象的值，value内容中仍然可以包含Ref对象，即可以嵌套"
    )
    title: str = Field(
        title="引用标题",
        description="生成引用链接的标题"
    )
    type: str = Field(
        title="可引用类型",
        description="可引用类型，如变量（var）、卡片（card）等",
        default="var"
    )
    description: Optional[str] = Field(
        title="描述信息",
        description="描述信息，相当于对该对象内容的概括，用于指导LLM引用",
        default=None
    )
    readable: bool | str | list[str] = Field(
        title="对应value对LLM是否可读",
        description="LLM不可读相当于只会将该对象的引用符号拼接到LLM的提示词，否则引用符合以及value的完整内容都会放进提示词",
        default=False
    )
    format: Optional[str] = Field(
        title="数据格式",
        description="该对象取值的格式，只在readable=True的时候有效",
        default=None
    )

    @staticmethod
    def validate_refs(obj):
        """递归验证并转换对象中的所有符合 Ref 结构的数据为 Ref 实例。

        本函数会深度遍历任意层级的对象（包括 BaseModel、dict、list、tuple 等），
        并尝试将符合 Ref 数据结构的字典对象转化为 Ref 模型实例。
        如果遇到嵌套结构，会继续递归处理其内部的 value 字段。

        示例：
        输入：{"reference1": {"title": "Some ID List", "value": [1, 2, 3]}}
        输出：{"reference1": Ref(title="Some ID List", value=[1, 2, 3])}

        Args:
            obj: 任意类型的输入对象，可能是 Ref、BaseModel、dict、list、tuple 或其他。

        Returns:
            处理后的对象，其中所有可解析为 Ref 的部分均已被转化为 Ref 实例。
        """
        if isinstance(obj, Ref):
            obj.value = Ref.validate_refs(obj.value)
            return obj
        elif isinstance(obj, BaseModel):
            return {
                k: Ref.validate_refs(getattr(obj, k))
                for k in obj.__class__.model_fields.keys()
            }
        elif isinstance(obj, Dict):
            try:
                a = Ref.model_validate(obj)
                a.value = Ref.validate_refs(a.value)
                return a
            except ValidationError:
                return {
                    k: Ref.validate_refs(v)
                    for k, v in obj.items()
                }
        elif isinstance(obj, list):
            return [
                Ref.validate_refs(i)
                for i in obj
            ]
        else:
            return obj

    @staticmethod
    def dump_refs(obj, remove_refs: bool = False):
        """递归展开 Ref 对象，提取其内部的原始值。

        若 `remove_refs=True`，则直接去除 Ref 外壳，仅保留其中的 value；
        否则，保留 Ref 结构，只在 value 内部递归处理。

        Args:
            obj: 任意类型的输入对象（可能包含 Ref、BaseModel、dict、list、tuple 等）。
            remove_refs (bool): 是否移除 Ref 包装，仅返回 value 部分。默认为 False。

        Returns:
            处理后的对象，其内部所有 Ref.value 均已被递归提取。
        """
        if remove_refs and isinstance(obj, Ref):
            return Ref.dump_refs(obj.value, remove_refs)

        if isinstance(obj, BaseModel):
            return {
                k: Ref.dump_refs(getattr(obj, k), remove_refs)
                for k in obj.__class__.model_fields.keys()
            }
        elif isinstance(obj, Dict):
            return {
                k: Ref.dump_refs(v, remove_refs)
                for k, v in obj.items()
            }
        elif isinstance(obj, (List, Tuple)):
            return [
                Ref.dump_refs(i, remove_refs)
                for i in obj
            ]
        else:
            return obj

    @staticmethod
    def parse_refs(obj, path: str = "") -> OrderedDict[str, "Ref"]:
        """解析对象中的所有 Ref 实例，并返回一个路径到 Ref 的有序映射。

        该函数会递归遍历对象结构（BaseModel、dict、list、tuple 等），
        为每个遇到的 Ref 记录其在层级结构中的路径（类似文件路径格式）。
        用于后续渲染引用索引或生成可视化文档。

        Args:
            obj: 待解析的对象，可能是 BaseModel、dict、list、tuple 或 Ref。
            path (str): 起始路径前缀，默认为空字符串。

        Returns:
            OrderedDict[str, Ref]: 一个有序字典，键为引用路径（如 "/a/b/1"），值为对应的 Ref 实例。
        """
        results = OrderedDict()

        def _parse_refs(_obj, _path: str):
            if isinstance(_obj, Ref):
                results[_path] = _obj
                _parse_refs(_obj.value, _path)
            elif isinstance(_obj, BaseModel):
                for name in _obj.model_fields_set:
                    value = getattr(_obj, name)
                    _parse_refs(value, f"{_path}/{name}")
            elif isinstance(_obj, Dict):
                for name, value in _obj.items():
                    _parse_refs(value, f"{_path}/{name}")
            elif isinstance(_obj, (List, Tuple)):
                for name, value in enumerate(_obj, start=1):
                    _parse_refs(value, f"{_path}/{name}")

        _parse_refs(obj, path)
        return results

    @staticmethod
    def render_refs(
            refs: OrderedDict[str, "Ref"],
            start_level: int = 0,
            delimiter: str = "\n"
    ) -> str:
        """将 Ref 对象的映射渲染为可读的 Markdown 格式字符串。

        每个 Ref 会被格式化为一个 Markdown 段落，包含：
        - 标题及引用链接，如 `[Title](type://path)`
        - 可选的描述（description）
        - 若 readable=True，则附带其内容的代码块（根据 format 自动选择 json 或文本）

        Args:
            refs (OrderedDict[str, Ref]): 路径与 Ref 实例的映射。
            start_level (int): Markdown 标题起始层级（如 0 表示从 `#` 开始，1 表示从 `##` 开始）。
            delimiter (str): 各引用之间的分隔符，默认为换行符。

        Returns:
            str: 生成的 Markdown 文本。
        """
        levels = {}
        all_path = {*refs}
        buffer = io.StringIO()
        for i, (path, ref) in enumerate(refs.items()):
            if i != 0:
                buffer.write(delimiter)

            level = Ref._compute_level(path, all_path, levels)
            buffer.write("#" * (level + start_level))
            buffer.write(" ")
            buffer.write(f"[{ref.title}]({ref.type}://{path})")
            buffer.write("\n")

            if ref.description:
                buffer.write(ref.description)
                buffer.write("\n")

            if ref.readable:
                fmt = ref.format
                v = Ref.dump_refs(ref.value, remove_refs=True)

                if isinstance(ref.readable, str):
                    v = v[ref.readable]
                elif isinstance(ref.readable, list):
                    v = {name: v[name] for name in ref.readable}

                if fmt is None:
                    if isinstance(v, (Dict, List, Tuple)):
                        fmt = "json"
                    else:
                        fmt = ""
                if fmt == "json":
                    v = json.dumps(v, ensure_ascii=False)
                buffer.write(f"```{fmt}\n")
                buffer.write(v)
                buffer.write("\n```")
                buffer.write("\n")

        return buffer.getvalue()

    @staticmethod
    def _compute_level(path: str, all_path: set[str], cache: dict[str, int]) -> int:
        if path in cache:
            return cache[path]

        level = int(path in all_path)
        if (i := path.rfind("/")) > 0:
            level += Ref._compute_level(path[:i], all_path, cache)
        cache[path] = level
        return level

    @staticmethod
    def read_ref(obj, path: str):
        """根据路径解析对象结构，返回指定路径对应的值。

        支持访问嵌套结构（BaseModel、dict、list、tuple）以及嵌套 Ref.value。
        路径格式类似于文件路径，例如：
            - "var://a/b/1"
            - "/a/b/1"

        若路径不存在，返回 None。

        Args:
            obj: 待查询的对象结构，可能包含 Ref、BaseModel、dict、list、tuple 等。
            path (str): 引用路径，可以包含协议前缀（如 "var://path/to/value"）。

        Returns:
            Any: 指定路径对应的值；若路径无效，返回 None。
        """
        if (s := path.find("://")) >= 0:
            path = path[s + 3:]

        for name in path.strip("/").split("/"):
            try:
                while True:
                    obj = Ref.model_validate(obj).value
            except ValidationError:
                pass

            if isinstance(obj, Dict):
                try:
                    obj = obj[name]
                except KeyError:
                    return None
            elif isinstance(obj, BaseModel):
                try:
                    obj = getattr(obj, name)
                except AttributeError:
                    return None
            elif isinstance(obj, (List, Tuple)):
                try:
                    index = max(0, int(name) - 1)
                    obj = obj[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        try:
            while True:
                obj = Ref.model_validate(obj).value
        except ValidationError:
            pass

        return obj


class ToolResponse(Response):
    """工具响应对象，建议所有的工具的response都继承自这个类"""

    model_config = ConfigDict(extra="allow")

    response_text: Optional[str] = Field(
        title="响应文本内容",
        description="响应文本内容，表示工具输出的非结构化信息。",
        default=None
    )
    metadata: Optional[Dict[str, Any]] = Field(
        title="结构化信息",
        description="工具输出的结构化信息，比如ID列表、链接列表",
        default=None
    )
    append_refs: bool = Field(
        title="追加可引用对象",
        description="追加metadata中的可引用对象（Ref）到response_text，这些Ref对象将被转化成markdown格式",
        default=True
    )
    summary_constraints: Optional[Union[str, List[str]]] = Field(
        title="总结约束条件",
        description="如果这个工具的结果需要进行整合，必须要满足的约束条件（这些条件是用自然语言描述的）。",
        default=None
    )
    skip_summarize: bool = Field(
        title="跳过总结环节",
        description=(
            "跳过总结环节，直接将内容输出。"
            "默认情况下不建议直接输出工具结果，因为直接输出可能存在安全隐患，并且结果比较生硬。"
        ),
        default=False
    )

    def model_post_init(self, __context: Any) -> None:
        if isinstance(self.summary_constraints, str):
            self.summary_constraints = [self.summary_constraints]

        if self.metadata:
            self.metadata = Ref.validate_refs(self.metadata)

    def parse_refs(self, path: str = "") -> OrderedDict[str, Ref]:
        return Ref.parse_refs(self.metadata, path)

    def render_refs(self, path: str = "", start_level: int = 0) -> str:
        return Ref.render_refs(self.parse_refs(path), start_level=start_level)


class SystemProfile(BaseModel):
    """Agent或其子模块自身的画像信息"""

    model_config = ConfigDict(extra="allow")

    description: str = Field(
        title="角色描述信息",
        description=(
            "用于为通用模块指定角色信息，针对特定的业务进行更详细的功能描述。"
            "例如对于销售类智能体中的任务规划模块，可以通过角色描述设置该模块每次以“导购”的角色来完成任务。"
        )
    )
    language: Optional[str] = Field(
        title="语言",
        description="模块所使用的语言",
        default=None
    )
    datetime: Optional[str] = Field(
        title="当前的时间日期",
        description="当前的时间日期，如果为空表示以当前时间为准",
        default=None
    )
    capabilities: Optional[List[str]] = Field(
        title="能力范畴",
        description=(
            "该模块的能力范畴（如能完成什么任务），可分条描述。"
        ),
        default=None
    )
    constrains: Optional[List[str]] = Field(
        title="条件约束",
        description="该模块的约束条件（如立场原则、特殊规则），可分条描述",
        default=None
    )
    extra_prompt: Optional[str] = Field(
        title="额外提示词",
        description="追加到标准提示词之后的额外提示词，在没有特殊需要的时候不建议使用",
        default=None
    )


class FewShot(BaseModel):
    """示例对象"""

    model_config = ConfigDict(extra="allow")

    input: str = Field(
        title="输入内容",
        description="示例对应的输入内容"
    )
    output: str = Field(
        title="输入内容",
        description="示例对应的输出内容"
    )
    thinking: Optional[str] = Field(
        title="思考过程",
        description="得到对应输出的思考过程（如有）",
        default=None
    )


class BasicKnowledge(BaseModel):
    type: Literal["base"] = "basic"
    content: str


class ToolKnowledge(BasicKnowledge):
    type: Literal["tool"] = "tool"
    tool_name: str | list[str] | None = None


class DecompositionKnowledge(BasicKnowledge):
    type: Literal["decomposition"] = "decomposition"


class SubtaskKnowledge(BasicKnowledge):
    type: Literal["subtask"] = "subtask"
    subtask: str | list[str] | None = None


DomainKnowledge = BasicKnowledge | ToolKnowledge | DecompositionKnowledge | SubtaskKnowledge


class SystemMemory(BaseModel):
    """系统级（System Level）记忆"""

    model_config = ConfigDict(extra="allow")

    few_shots: Optional[List[FewShot]] = Field(
        title="示例",
        description="针对当前任务的示例，可以是Agent设计者预先给出",
        default=None
    )
    domain_knowledge: Optional[List[str | DomainKnowledge]] = Field(
        title="领域知识",
        description="针对当前任务的领域知识，主要由于Agent设计者预先给出",
        default=None
    )
    reflections: Optional[List[str]] = Field(
        title="反思信息",
        description="针对当前任务的反思信息，主要由反思模块根据Agent历史表现总结得到",
        default=None
    )


class UserMemory(BaseModel):
    """用户级（User Level）记忆"""

    model_config = ConfigDict(extra="allow")

    user_id: str = Field(
        title="用户标识",
        description="用户标识",
        default="default_user"
    )
    user_preference: Optional[Dict[str, str]] = Field(
        title="用户偏好",
        description="基于所有历史行为总结出的用户偏好信息",
        default=None
    )
    user_profile: Optional[Dict[str, str]] = Field(
        title="用户画像",
        description="基于所有历史行为总结出的用户画像信息",
        default=None
    )


class ChatMessage(BaseModel):
    """对话消息"""

    model_config = ConfigDict(extra="allow")

    content: str = Field(
        title="消息内容",
        description=(
            "整合了各种结构化信息（文本、链接以及表格等）的最终消息内容。"
            "这些结构化信息一般在metadata中给出。"
            "整合过程往往是业务相关的，可以构造专门用于整合的模块来完成。"
        )
    )
    metadata: Optional[Dict[str, Any]] = Field(
        title="消息元数据",
        description="该字典的key为对应数据项的名称，value必须是标准JSON类型。如果该属性为空，表示消息内容只以content为准。",
        default=None
    )
    role: str = Field(
        title="角色",
        description="发出该消息的角色"
    )
    turn_id: Optional[int] = Field(
        title="轮次标识",
        description="对应对话消息的轮次标识",
        default=None
    )
    thinking: Optional[str] = Field(
        title="思考过程",
        description="产生该对话消息时的思考内容（如有）",
        default=None
    )


class Mention(BaseModel):
    """用户提及信息"""

    model_config = ConfigDict(extra="allow")

    type: str = Field(
        title="提及信息的类型",
        description="如“关键字”、“实体”、“解析后的实体”等"
    )
    name: str = Field(
        title="提及信息的名称",
        description="一般是与业务相关的提及信息描述，如“提及商品”、“提及人名”等，该信息可能会被某些算法作为LLM提示的一部分"
    )
    content: Union[str, List[str]] = Field(
        title="提及内容",
        description="用户提及的内容，例如用户感兴趣的话题、实体等"
    )
    span: list[int] | None = Field(
        title="位置信息",
        description="提及内容在原始query中的位置信息",
        default=None
    )
    role: str = Field(
        title="角色",
        description="必须明确指定角色",
    )
    turn_id: Optional[int] = Field(
        title="轮次标识",
        description="对应提及信息的轮次标识",
        default=None
    )


class SessionMemory(BaseModel):
    """会话级（Session Level）记忆"""

    model_config = ConfigDict(extra="allow")

    chat_history: List[ChatMessage] = Field(
        title="对话历史",
        description="当前会话的历史对话信息，默认为空列表",
        default_factory=list
    )
    mentions: Optional[List[Mention]] = Field(
        title="用户提及信息",
        description="当前会话中所有用户提及信息",
        default_factory=list
    )
    session_preference: Optional[Dict[str, str]] = Field(
        title="用户偏好",
        description="当前会话的用户偏好信息",
        default=None
    )

    def get_messages(self, role: Optional[str] = None) -> List[ChatMessage]:
        return [
            m for m in self.chat_history
            if m.role == role
        ] if role is not None else self.chat_history

    def get_mentions(
            self,
            role: Optional[str] = None,
            type_: Optional[str] = None,
            name: Optional[str] = None
    ) -> List[Mention]:
        return [
            m for m in self.mentions
            if (
                    (role is None or m.role == role) and
                    (type_ is None or m.type == type_) and
                    (name is None or m.name == name)
            )
        ]


class NDArray(BaseModel):
    """多维数组，可与numpy.ndarray相互转换"""

    data: str = Field(
        title="数组数据",
        description="数组数据（base64编码的二进制数据）"
    )
    dtype: str = Field(
        title="数据类型",
        description="数据类型"
    )
    shape: Tuple[int, ...] = Field(
        title="数组shape",
        description="数组shape（支持高维数组）"
    )

    @classmethod
    def from_array(cls, a: np.ndarray):
        bin_data = a.tobytes("C")
        return cls(
            data=base64.b64encode(bin_data).decode("utf-8"),
            dtype=str(a.dtype),
            shape=a.shape
        )

    def to_array(self) -> np.ndarray:
        bin_data = base64.b64decode(self.data)
        return np.frombuffer(
            buffer=bin_data,
            dtype=self.dtype
        ).reshape(self.shape)


class CSRArray(BaseModel):
    """稀疏数组，可与scipy.sparse.csr_array相互转换"""

    data: List[Union[int, float]] = Field(
        title="数组数据",
        description="数组数据（数据的列表）"
    )
    indices: List[int] = Field(
        title="索引序号",
        description="索引序号"
    )
    indptr: List[int] = Field(
        title="行数据范围",
        description="行数据范围"
    )
    dtype: str = Field(
        title="数据类型",
        description="数据类型"
    )
    shape: Tuple[int, int] = Field(
        title="数组shape",
        description="数组shape（仅支持二维数组）"
    )

    @classmethod
    def from_array(cls, a: csr_array):
        return cls(
            data=a.data,
            indices=a.indices,
            indptr=a.indptr,
            dtype=str(a.dtype),
            shape=a.shape
        )

    def to_array(self) -> csr_array:
        return csr_array(
            (self.data, self.indices, self.indptr),
            dtype=self.dtype,
            shape=self.shape
        )


class FieldSchema(BaseModel):
    """知识集合属性（列）模式"""

    model_config = ConfigDict(extra="allow")

    field_name: str = Field(
        title="属性名（列名）",
        description="属性名（列名），不要以下划线开头，下划线开头的都是内部名称。"
    )
    field_type: Literal[
        "INT64",
        "VARCHAR",
        "FLOAT_VECTOR",
        "SPARSE_FLOAT_VECTOR",
    ] = Field(
        title="属性数据类型",
        description="属性数据类型。"
    )
    index_type: Literal["Trie", "HNSW", "SPARSE_WAND"] = Field(
        title="索引类型",
        description="向量属性的索引类型，目前只支持3种。",
        default=None
    )
    index_params: Optional[Dict[str, Any]] = Field(
        title="索引参数",
        description="针对特定索引类型所指定的参数，如果索引参数为空，则表示使用对应索引类型的默认参数。",
        default=None
    )
    is_primary: bool = Field(
        title="是否是主键",
        description="该列是否是主键。",
        default=False,
    )
    auto_id: bool = Field(
        title="是否是自动ID",
        description="该列是否是自动生成的ID属性。",
        default=False
    )
    dim: int = Field(
        title="向量维度",
        description="文档中包含的向量的维度。",
        default=-1
    )
    max_length: int = Field(
        title="VARCHAR最大长度",
        description="如果类型指定为VARCHAR，则max_length表示其最大长度。如果数据类型不是VARCHAR则该项无效。",
        default=65_535,
    )

    # class var
    _DEFAULT_INDEX_PARAMS = {
        "HNSW": {"metric_type": "L2", "params": {"M": 8, "efConstruction": 64}},
        "SPARSE_WAND": {"metric_type": "IP"}
    }

    def model_post_init(self, __context: Any) -> None:
        if not self.index_params:
            self.index_params = self._DEFAULT_INDEX_PARAMS.get(self.index_type)


class Property(BaseModel):
    """工具属性信息"""

    # model_config = ConfigDict(extra="allow")

    description: Optional[str] = Field(
        title="属性描述",
        description="属性描述",
        default=None
    )
    type: Optional[str] = Field(
        title="数据类型",
        description="该属性的数据类型，通常为object, array, string, integer, float, bool或null",
        default=None
    )
    anyOf: Optional[List["Property"]] = Field(
        title="Union类型",
        description="有多种类型可选，相当于python的Union类型",
        default=None
    )
    properties: Optional[Dict[str, "Property"]] = Field(
        title="子属性信息",
        description="如果属性类型为object，该项为其子属性信息",
        default=None
    )
    items: Optional["Property"] = Field(
        title="数组元素属性信息",
        description="如果属性类型为array，该项为其元素的属性信息",
        default=None
    )
    enum: Optional[List[str]] = Field(
        title="枚举值",
        description="如果该类型的取值范围为有限字符串集合，则这里枚举出所有的可选值。",
        default=None
    )
    required: Optional[List[str]] = Field(
        title="子属性中的必要属性",
        description="子属性中的必要属性",
        default=None
    )


class Tool(BaseModel):
    """工具描述"""

    model_config = ConfigDict(extra="allow")

    name: str = Field(
        title="工具名称",
        description="工具名称"
    )
    description: Optional[str] = Field(
        title="工具描述",
        description="工具的功能描述",
        default=None
    )
    input_schema: Optional[Property] = Field(
        title="工具参数信息",
        description="工具的参数信息",
        default=None
    )


class Intent(BaseModel):
    """候选意图描述"""

    model_config = ConfigDict(extra="allow")

    name: str = Field(
        title="意图名称",
        description="意图名称，可以用一个词或短语表示，也可以是一句话"
    )
    description: Optional[str] = Field(
        title="意图描述",
        description="意图详细描述",
        default=None
    )


class ToolCalling(BaseModel):
    """工具调用信息"""

    model_config = ConfigDict(extra="allow")

    name: str = Field(
        title="工具名称",
        description="被调用工具的名称"
    )
    arguments: Dict[str, Union[str, int, float, bool, Dict, List, "ToolCalling", None]] = Field(
        title="调用参数",
        description=(
            "参数名->参数值，参数值有3种情况："
            "为字符串时表示正常参数，需要执行模块转换成对应数据类型，例如json或python的eval()；"
            "为ToolCalling对象时候，表示依赖该工具调用输出的结果；"
            "为空表示不确定，需要执行模块动态解析"
        ),
        default_factory=dict
    )
    id: Optional[str] = Field(
        title="工具调用ID",
        description="工具调用的标识符，如果这里不指定该值，则规划模块会自动生成，但仍然建议在构建ToolCalling时就给出此ID",
        default=None
    )
    fallback: Optional[str] = Field(
        title="兜底信息",
        description="工具调用失败后返回的内容",
        default=None
    )


class Plan(BaseModel):
    """任务规划结果"""

    model_config = ConfigDict(extra="allow")

    tool_callings: List[ToolCalling] = Field(
        title="工具调用序列",
        description="完成相应任务的工具调用序列",
        default_factory=list
    )
    content: Optional[str] = Field(
        title="消息内容",
        description=(
            "该消息可以带有以下信息："
            "（1）需要用户澄清的问题，比如用户给出的任务描述不完整或者有歧义，可先不调用工具，先通过提问让用户在下一轮对话中给出相关信息，"
            "此时ToolCalling列表为空；"
            "（2）生成该计划（工具调用序列）的思考过程，当然也可以将思考过程放到PlanningResponse中返回。"
        ),
        default=None
    )


class ExecutionError(BaseModel):
    """执行错误信息对象"""

    model_config = ConfigDict(extra="allow")

    message: str = Field(
        title="错误信息",
        description="错误信息"
    )
    error: Optional[str] = Field(
        title="错误名称",
        description="通常是系统中捕获的异常的名称",
        default=None
    )
    traceback: Optional[str] = Field(
        title="详细信息",
        description="错误相关的详细信息，如函数调用栈信息等，用于定位错误",
        default=None
    )


class ExecutionStatus(BaseModel):
    """执行状态信息对象"""

    model_config = ConfigDict(extra="allow")

    name: str = Field(
        title="工具名称",
        description="被执行工具的名称"
    )
    result: Optional[Any] = Field(
        title="执行结果",
        description="工具执行结果",
        default=None
    )
    error: Optional[ExecutionError] = Field(
        title="错误信息",
        description="工具执行错误信息，如果错误信息不为空，则执行结果无效",
        default=None
    )


class Observation(BaseModel):
    """观测信息对象

    观测信息对象的主要用途有以下几个：
    （1）用于给Summarization进行整合；
    （2）回传给一次性Planning模块进行重新规划；
    （3）回传给迭代式Planning模块进行下一步规划的生成；
    （4）可写进SessionMemory.chat_history用于保持上下文。
    """

    model_config = ConfigDict(extra="allow")

    plan: Plan = Field(
        title="规划方案",
        description="规划方案一般由Planning模块给出，进而被Execution模块执行"
    )
    status: List[ExecutionStatus] = Field(
        title="执行状态序列",
        description="列表中每一个元素对应Plan中的每一个ToolCalling对象",
        default_factory=list
    )


class LLMConfig(BaseModel):
    """大模型服务配置"""

    model_config = ConfigDict(extra="allow")

    base_url: str = Field(
        title="服务地址",
        description="服务地址"
    )
    model: str = Field(
        title="模型名称",
        description="一个地址可能对应多个模型，需要指定模型名称"
    )
    api_key: Optional[str] = Field(
        title="API密钥",
        description="如果启动大模型服务的时候没有指定，这里就不需要",
        default=None
    )


class GenerationOptions(BaseModel):
    """LLM生成的相关选项"""

    model_config = ConfigDict(extra="allow")

    model_name: Optional[str] = Field(
        title="模型名称",
        description="生成所依赖的大模型名称，默认情况下无需指定大模型；但如果指定了具体模型，则表示这组生成参数和LLM具有较强的依赖关系。",
        default=None
    )
    temperature: Optional[float] = Field(
        title="采样温度",
        description="如果为空或者0，表示不采样",
        default=None,
        ge=0.0
    )
    max_tokens: int = Field(
        title="最大Token数",
        description="该次生成过程中所使用的最大Token数量",
        default=2048
    )
    stop_token_ids: List[int] = Field(
        title="终止Token ID",
        description="只要生成到相应的Token就结束生成",
        default_factory=list
    )
    top_p: Optional[float] = Field(
        title="积累概率阈值",
        description=(
            "对应核采样中的积累概率阈值。"
            "解释：将大模型预测的词元按概率从高到低排序，选取其累计概率刚好超过 top_p 的最小词元集合，作为最终的采样候选集。"
            "top_p越大候选词元集合越大，生成结果多样性越强；反之候选集合越小，生成结果越确定。"
        ),
        ge=0.0,
        le=1.0,
        default=None
    )
    verbosity: str | None = Field(
        title="暴露推理细节",
        description="取值为`none`, `low`, `medium`和`high`之一",
        default=None
    )


class MCPServerConfig(BaseModel):
    """MCP服务器的配置对象"""

    model_config = ConfigDict(extra="allow")

    url: str = Field(
        title="URL",
        description="MCP服务的URL"
    )
    type: str = Field(
        title="服务类型",
        description="服务类型，如：`sse`, `streamable_http`, `libentry`。",
        default="libentry"
    )
    endpoint: str = Field(
        title="入口",
        description="访问MCP服务的入口，空字符串表示默认入口，如`/sse`。",
        default=""
    )
    enabled: bool = Field(
        title="是否开启",
        description="是否开启",
        default=True
    )
    auth: Optional[Dict[str, Any]] = Field(
        title="验证信息",
        description="验证信息",
        default=None
    )


class TaskSubmissionRequest(Request):
    """提交任务"""

    __request_name__ = "submit_task"


class TaskSubmissionResponse(Response):
    """提交任务"""

    task_id: str = Field(
        title="任务ID",
        description="任务ID"
    )


class TaskStatusRequest(Request):
    """获取任务状态"""

    task_id: str = Field(
        title="任务ID",
        description="需要查询的任务唯一标识"
    )
    stream: bool = Field(
        title="流式输出",
        description=(
            "是否使用流式输出模式。"
            "如果为True，则请求会持续返回任务的状态，直到任务结束。"
            "（该请求的输出流中断不会影响任务本身的执行）"
        ),
        default=False
    )


class TaskStatusResponse(Response):
    """获取任务状态"""

    task_id: str = Field(
        title="任务ID",
        description="任务的唯一标识"
    )
    progress: float = Field(
        title="任务进度",
        description="任务当前的进度, 取值范围在[0, 1]之间",
        default=0.0,
        ge=0.0,
        le=1.0
    )
    error: Optional[str] = Field(
        title="错误信息",
        description="任务执行过程中发生的错误信息；如果无错误则为None",
        default=None
    )
    finished: bool = Field(
        title="是否完成",
        description="标识任务是否已完成；True表示已完成，False表示未完成",
        default=False
    )

    def model_post_init(self, context):
        if self.finished:
            self.progress = 1.0


class TaskCancelingRequest(Request):
    """取消任务"""

    task_id: str = Field(
        title="任务ID",
        description="需要取消的任务唯一标识"
    )


class TaskCancelingResponse(Response):
    """取消任务"""

    task_id: str = Field(
        title="任务ID",
        description="被取消的任务唯一标识"
    )
