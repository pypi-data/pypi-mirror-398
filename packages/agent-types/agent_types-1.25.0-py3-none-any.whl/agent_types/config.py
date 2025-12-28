#!/usr/bin/env python3

__author__ = "xi"
__all__ = [
    "ListConfigRequest",
    "ListConfigResponse",
    "ReadConfigRequest",
    "ReadConfigResponse",
    "WriteConfigRequest",
    "WriteConfigResponse",
    "DeleteConfigRequest",
    "DeleteConfigResponse",
    "DropConfigRequest",
    "DropConfigResponse",
]

from typing import Any, Dict, List, Optional, Union

from pydantic import ConfigDict, Field

from agent_types.common import Request, Response


class ListConfigRequest(Request):
    """列出所有配置项请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "list_config"

    config_id: str = Field(
        title="配置标识",
        description="配置标识，一组配置相当于一些列配置项的集合，不同的配置标识可用于区分不同的环境，如dev, testing, prod等等。",
        default="default"
    )
    prefix: Optional[str] = Field(
        title="配置名称前缀",
        description="要列出的配置名称前缀，例如`llm.`或`llm`都可以表示列出所有以`llm.`为名称前缀的配置项。",
        default=None
    )


class ListConfigResponse(Response):
    """列出所有配置项响应"""

    model_config = ConfigDict(extra="allow")

    config: Optional[Union[Dict[str, Any], List[str]]] = Field(
        title="所有配置项",
        description="所有配置项，如果对应配置标识的配置不存在，则返回空。可以返回完整的配置项（dict）也可以仅返回配置项名称（list）。",
        default=None
    )


class ReadConfigRequest(Request):
    """读取配置项请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "read_config"

    name: str = Field(
        title="配置项名称",
        description="配置项名称，配置项名称在整个配置中必须唯一。"
    )
    config_id: str = Field(
        title="配置标识",
        description="配置标识，一组配置相当于一些列配置项的集合，不同的配置标识可用于区分不同的环境，如dev, testing, prod等等。",
        default="default"
    )


class ReadConfigResponse(Response):
    """读取配置项响应"""

    model_config = ConfigDict(extra="allow")

    value: Any = Field(
        title="配置项取值",
        description="配置项取值，如果配置不存在可以（1）返回空值；（2）抛出异常；具体行为以具体实现为准。"
    )


class WriteConfigRequest(Request):
    """写入配置项请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "write_config"

    name: str = Field(
        title="配置项名称",
        description="配置项名称，配置项名称在整个配置中必须唯一。"
    )
    value: Any = Field(
        title="配置项取值",
        description="配置项取值，不能为空。"
    )
    config_id: str = Field(
        title="配置标识",
        description="配置标识，一组配置相当于一些列配置项的集合，如果不存在会创建一组新的配置。",
        default="default"
    )


class WriteConfigResponse(Response):
    """写入配置项响应"""

    model_config = ConfigDict(extra="allow")


class DeleteConfigRequest(Request):
    """删除配置项请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "delete_config"

    name: str = Field(
        title="配置项名称",
        description="配置项名称，配置项名称在整个配置中必须唯一。"
    )
    config_id: str = Field(
        title="配置标识",
        description="配置标识，一组配置相当于一些列配置项的集合，不同的配置标识可用于区分不同的环境，如dev, testing, prod等等。",
        default="default"
    )


class DeleteConfigResponse(Response):
    """删除配置项响应"""

    model_config = ConfigDict(extra="allow")


class DropConfigRequest(Request):
    """删除所有配置项请求"""

    model_config = ConfigDict(extra="allow")
    __request_name__ = "drop_config"

    config_id: str = Field(
        title="配置标识",
        description="配置标识，一组配置相当于一些列配置项的集合，不同的配置标识可用于区分不同的环境，如dev, testing, prod等等。",
        default="default"
    )
    auth_key: Optional[str] = Field(
        title="安全校验口令",
        description=(
            "删除属于危险操作，建议搭配安全检验口令。"
            "这个口令可以是在服务启动的时候由管理员设置的，在服务实现删除操作的逻辑中，增加安全口令的验证。"
            "当然，如果不怕危险也可以忽略这个参数。"
        ),
        default=None
    )


class DropConfigResponse(Response):
    """删除所有配置项响应"""

    model_config = ConfigDict(extra="allow")

    num_deleted: int = Field(
        title="删除的配置项数量",
        description="删除的配置项数量，如果要删除的配置不存在，则返回0"
    )
