"""FastMCP数据模型定义"""
from typing import Optional
from pydantic import BaseModel, Field

class FileObject(BaseModel):
    """文件对象模型"""
    path: str = Field(description="文件URL，必须包含协议，支持http/https/oss")
    password: Optional[str] = Field(None, description="文档密码，如果文档受密码保护则需要提供")
    name: Optional[str] = Field(None, description="原始文件名") 