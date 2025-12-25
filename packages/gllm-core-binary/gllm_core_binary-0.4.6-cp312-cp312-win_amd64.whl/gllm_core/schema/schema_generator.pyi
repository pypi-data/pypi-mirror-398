from gllm_core.utils.analyzer import analyze_method as analyze_method
from pydantic import BaseModel as BaseModel
from typing import Callable

def generate_params_model(method: Callable, class_name: str) -> type[BaseModel]:
    '''Generate a Pydantic model representing a component method signature.

    The generated class is named `{class_name}Params` and contains one field for
    every parameter in `method`. The first `self` parameter is ignored, `*args` are
    skipped entirely, and `**kwargs` trigger `extra="allow"` to permit arbitrary
    keyword arguments at runtime.

    For legacy `_run` methods with only `**kwargs`, this function will use
    RunAnalyzer to infer parameters from the method body usage patterns.

    Args:
        method (Callable): Method whose signature should be represented.
        class_name (str): Component class name used to derive the generated model name.

    Returns:
        type[BaseModel]: A Pydantic `BaseModel` subclass describing the method\'s
            parameters.

    Example:
        ```python
        class_name = "TextProcessor"

        def process(self, text: str, count: int = 5) -> str:
            return text * count

        Model = generate_params_model(process, class_name)
        assert Model.__name__ == "TextProcessorParams"
        assert Model(text="hello", count=2).model_dump() == {"text": "hello", "count": 2}
        ```
    '''
