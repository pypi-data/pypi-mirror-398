from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class ToolUsage(BaseModel):
    """Tool level token usage information"""

    tool_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    metadata: Optional[Dict[str, Any]] = None


class NodeUsage(BaseModel):
    """Node level token usage information"""

    node_name: str
    model_name: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    tools: Optional[List[ToolUsage]] = None
    metadata: Optional[Dict[str, Any]] = None


class TokenUsage(BaseModel):
    """Overall token usage information"""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    nodes: List[NodeUsage]
    metadata: Optional[Dict[str, Any]] = None
