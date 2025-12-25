from gllm_core.schema.tool import Tool as Tool
from typing import Any, Callable

def from_google_function(function_declaration: Any, func: Callable | None = None) -> Tool:
    """Convert a Google ADK function declaration into the SDK Tool representation.

    The Google ADK `FunctionDeclaration` provides access to:
    1. `name`: The function name
    2. `description`: The function description
    3. `parameters`: A dict in JSON Schema format (OpenAPI 3.0 compatible)

    Args:
        function_declaration (Any): The Google ADK function declaration to convert.
        func (Callable | None, optional): The implementation function for the tool. Defaults to None.

    Returns:
        Tool: The converted SDK tool.

    Raises:
        ValueError: If the function declaration is None or has invalid fields.
        AttributeError: If required attributes are missing.
        TypeError: If field types are incorrect.
    """
