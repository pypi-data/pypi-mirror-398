from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# 文件信息模型
class FileInfo(BaseModel):
    name: str
    size: int
    modified: datetime

# Markdown文件列表响应
class FileListResponse(BaseModel):
    files: List[FileInfo]
    directory: str

# Markdown内容响应
class MarkdownContentResponse(BaseModel):
    content: str
    file: str

# 脚本块信息
class ScriptBlock(BaseModel):
    id: str
    title: str
    language: str
    code: str
    line_start: int
    line_end: int

# Markdown解析结果
class MarkdownParseResult(BaseModel):
    html: str
    scripts: List[ScriptBlock]

# 脚本执行请求
class ScriptExecuteRequest(BaseModel):
    script_id: str
    code: str

# 脚本输出消息
class ScriptOutputMessage(BaseModel):
    type: str  # stdout, stderr, exit, stdin_prompt, error
    content: str
    timestamp: str  # ISO 8601格式的时间戳字符串

# 脚本输入消息（从客户端发送到服务器）
class ScriptInputMessage(BaseModel):
    type: str = "input"  # 固定为"input"
    content: str  # 用户输入的内容

# 插件信息
class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    type: str
    css: Optional[str] = None
    js: Optional[str] = None
    terminalTheme: Optional[Dict[str, str]] = None