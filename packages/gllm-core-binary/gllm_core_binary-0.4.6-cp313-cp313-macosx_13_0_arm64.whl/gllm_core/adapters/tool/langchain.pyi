from _typeshed import Incomplete
from gllm_core.schema.tool import Tool as Tool
from typing import Any

class LangChainToolKeys:
    """Constants for LangChain tool attribute keys."""
    FUNC: str
    COROUTINE: str
    RUN: str
    ARUN: str
    NAME: str
    DESCRIPTION: str
    ARGS_SCHEMA: str

LANGCHAIN_FUNCTION_ATTRS: Incomplete

def from_langchain_tool(langchain_tool: Any) -> Tool:
    """Convert a LangChain tool into the SDK Tool representation.

    This function handles both traditional LangChain tools created with the @tool decorator
    and tools created by subclassing the LangChain Tool class.

    Args:
        langchain_tool (Any): The LangChain tool to convert.

    Returns:
        Tool: The converted SDK tool.

    Raises:
        ValueError: If the input is not a valid LangChain tool.
    """
