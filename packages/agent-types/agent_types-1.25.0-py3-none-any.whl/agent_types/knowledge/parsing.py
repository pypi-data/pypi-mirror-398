#!/usr/bin/env python3

__all__ = [
    "ParsingRequest",
    "ParsingResponse",
    "PDFParsingRequest",
    "PDFParsingResponse",
    "WordParsingRequest",
    "WordParsingResponse",
    "PPTParsingRequest",
    "PPTParsingResponse",
    "TableParsingRequest",
    "TableParsingResponse",
    "HTMLParsingRequest",
    "HTMLParsingResponse",
    "MarkdownParsingRequest",
    "MarkdownParsingResponse",
]

from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from agent_types.common import Request, Response


class ParsingRequest(Request):
    """解析文件"""

    __request_name__ = "parse_file"

    file_name: str = Field(
        title="文件名",
        description="文件名，带有后缀"
    )
    file_content_base64: Optional[str] = Field(
        title="文件内容",
        description="base64编码的文件内容",
        default=None
    )
    file_content_url: Optional[str] = Field(
        title="文件内容对应的URL",
        description="文件内容对应的URL，可以是本地路径，也可以是s3等远程路径",
        default=None
    )
    file_meta_info: Optional[Dict[str, Any]] = Field(
        title="文件元信息",
        description="文件的元信息, 例如文件的类别标签等",
        default=None
    )

    @model_validator(mode="after")
    def _check_file_content(self):
        if self.file_content_base64 is None and self.file_content_url is None:
            raise ValueError(
                "At least one of "
                "`file_content_base64` or `file_content_url` "
                "should be given.",
            )
        return self


class ParsingResponse(Response):
    """解析文件"""

    text: str = Field(
        title="解析文本",
        description="文档解析后返回的内容"
    )
    text_type: str = Field(
        title="文本类型",
        description="文本内容类型, `md`, `txt`, `json`",
        default="md"
    )


class PDFParsingRequest(ParsingRequest):
    """解析PDF文件"""

    __request_name__ = "parse_pdf"

    backend: str = Field(
        title="解析后端",
        description="解析后端,可选: pipeline, vlm-*",
        default="pipeline"
    )
    parse_method: Optional[str] = Field(
        title="解析方法",
        description="解析方法,可选: auto, txt, ocr",
        default="auto"
    )
    formula_enable: Optional[bool] = Field(
        title="公式解析",
        description="公式解析是否启用",
        default=True
    )
    table_enable: Optional[bool] = Field(
        title="表格解析",
        description="表格解析是否启用",
        default=True
    )
    is_save_image: Optional[bool] = Field(
        title="保存图片",
        description="是否保存图片",
        default=True
    )
    is_save_layout: Optional[bool] = Field(
        title="保存布局",
        description="是否保存布局信息",
        default=True
    )
    language: Optional[str] = Field(
        title="语言",
        description="语言,可选: ch, en,影响ocr效果",
        default="ch"
    )
    start_page_id: Optional[int] = Field(
        title="起始页码",
        description="起始页码",
        default=0
    )
    end_page_id: Optional[int] = Field(
        title="结束页码",
        description="结束页码",
        default=None
    )


class PDFParsingResponse(ParsingResponse):
    """解析PDF文件"""

    image_dir: Optional[str] = Field(
        title="图片目录",
        description="图片目录",
        default=None
    )
    layout_info_dir: Optional[Dict[str, Any]] = Field(
        title="布局信息目录",
        description="布局信息目录",
        default=None
    )


class WordParsingRequest(ParsingRequest):
    """解析Word文件"""

    __request_name__ = "word_parse"


class WordParsingResponse(ParsingResponse):
    """解析Word文件"""
    pass


class PPTParsingRequest(ParsingRequest):
    """解析PPT文件"""

    __request_name__ = "parse_ppt"

    slide_start_index: Optional[int] = Field(
        title="起始幻灯片索引",
        description="幻灯片起始索引",
        default=0
    )
    slide_end_index: Optional[int] = Field(
        title="结束幻灯片索引",
        description="幻灯片结束索引",
        default=None
    )
    is_save_image: Optional[bool] = Field(
        title="保存图片",
        description="是否保存图片",
        default=False
    )
    is_save_video: Optional[bool] = Field(
        title="保存视频",
        description="是否保存视频",
        default=False
    )
    is_save_audio: Optional[bool] = Field(
        title="保存音频",
        description="是否保存音频",
        default=False
    )


class PPTParsingResponse(ParsingResponse):
    """解析PPT文件"""

    image_dir: Optional[str] = Field(
        title="图片目录",
        description="幻灯片图片目录",
        default=None
    )
    video_dir: Optional[str] = Field(
        title="视频目录",
        description="PPT视频目录",
        default=None
    )
    audio_dir: Optional[str] = Field(
        title="音频目录",
        description="PPT音频目录",
        default=None
    )


class TableParsingRequest(ParsingRequest):
    """解析Excel、CSV等表格文件"""

    __request_name__ = "parse_table"

    sheet_list: Optional[List[str]] = Field(
        title="表格列表",
        description="表格列表,可指定要解析的sheet名称列表",
        default=None
    )


class TableParsingResponse(ParsingResponse):
    """解析Excel、CSV等表格文件"""

    table_image_dir: Optional[str] = Field(
        title="表格图片目录",
        description="表格图片目录",
        default=None
    )


class HTMLParsingRequest(ParsingRequest):
    """解析HTML文件"""

    __request_name__ = "parse_html"

    tag_rules: Optional[Dict[str, Any]] = Field(
        title="标签规则",
        description="标签规则",
        default=None
    )


class HTMLParsingResponse(ParsingResponse):
    """解析HTML文件"""

    image_dir: Optional[str] = Field(
        title="图片目录",
        description="HTML图片目录",
        default=None
    )
    video_dir: Optional[str] = Field(
        title="视频目录",
        description="HTML视频目录",
        default=None
    )
    audio_dir: Optional[str] = Field(
        title="音频目录",
        description="HTML音频目录",
        default=None
    )
    tag_info: Optional[Dict[str, Any]] = Field(
        title="标签信息",
        description="HTML标签抽取结果",
        default=None
    )


class MarkdownParsingRequest(ParsingRequest):
    """解析Markdown文件"""

    __request_name__ = "parse_markdown"

    convert_traditional: Optional[bool] = Field(
        title="繁体转换",
        description="是否将简体转换为繁体",
        default=True
    )
    optimize_format: Optional[bool] = Field(
        title="优化格式",
        description="是否优化Markdown格式",
        default=False
    )
    add_document_title: Optional[bool] = Field(
        title="添加文档标题",
        description="是否添加文档名增强",
        default=False
    )


class MarkdownParsingResponse(ParsingResponse):
    """解析Markdown文件"""
    pass
