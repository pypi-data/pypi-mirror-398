from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = False


class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(..., alias="inputSchema")


class ServerInfo(BaseModel):
    """Server information"""
    name: str
    version: str
    description: Optional[str] = None


class MCPConfig(BaseModel):
    """MCP configuration"""
    server: ServerInfo
    tools: List[Tool]
