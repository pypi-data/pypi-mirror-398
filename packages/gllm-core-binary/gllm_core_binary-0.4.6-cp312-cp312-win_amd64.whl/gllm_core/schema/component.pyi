from gllm_core.event.event_emitter import EventEmitter as EventEmitter
from gllm_core.schema.schema_generator import generate_params_model as generate_params_model
from gllm_core.schema.tool import Tool as Tool, tool as tool
from gllm_core.utils import BinaryHandlingStrategy as BinaryHandlingStrategy, binary_handler_factory as binary_handler_factory
from gllm_core.utils.analyzer import MethodSignature as MethodSignature, ParameterInfo as ParameterInfo, ParameterKind as ParameterKind, RunProfile as RunProfile, analyze_method as analyze_method
from gllm_core.utils.logger_manager import LoggerManager as LoggerManager
from gllm_core.utils.main_method_resolver import MainMethodResolver as MainMethodResolver
from pydantic import BaseModel as BaseModel
from typing import Any, Callable

def main(method: Callable) -> Callable:
    """Decorate a Component method as the async main entrypoint.

    Usage:
        Declare the coroutine that should act as the primary execution path
        for a `Component` subclass. The decorated coroutine will be resolved by
        `Component.run()` unless another subclass overrides the decoration.

    Args:
        method (Callable): Coroutine to mark as the main entrypoint.

    Returns:
        Callable: The same coroutine that is passed to the decorator. The decorator only marks the method as the main
            entrypoint. It does not wrap or change its behavior or signature.

    Raises:
        TypeError: If the decorated callable is not asynchronous.
    """

class Component:
    '''An abstract base class for all components used throughout the Gen AI applications.

    Every instance of Component has access to class-level `_default_log_level` and `_logger`, as detailed below.
    For components that require high observability, it is recommended to set `_default_log_level` to `logging.INFO`
    or higher.

    Defining Custom Components:
        There are two ways to define the main execution logic for a component:

        1. **Using the @main decorator (Recommended)**:
           Decorate an async method with `@main` to mark it as the primary entrypoint.
           This is the preferred approach as it provides explicit control over the main method.

           ```python
           class MyComponent(Component):
               _default_log_level = logging.INFO

               @main
               async def execute(self, **kwargs: Any) -> Any:
                   return "Hello from @main!"
           ```

        2. **Implementing _run method (Deprecated)**:
           Override the abstract `_run` method. This is the traditional approach and still supported.

           ```python
           class MyComponent(Component):
               _default_log_level = logging.INFO

               async def _run(self, **kwargs: Any) -> Any:
                   return "Hello, World!"
           ```

        The `run()` method resolves the main entrypoint using the following precedence:
        1. Method decorated with @main in the current class.
        2. Method decorated with @main in the nearest ancestor class.
        3. Method named in __main_method__ property.
        4. The _run method (with deprecation warning).

    Attributes:
        run_profile (RunProfile): The profile of the `_run` method.
            This property is used by `Pipeline` to analyze the input requirements of the component.
            In most cases, unless you are working with `Pipeline` and `PipelineStep`s, you will not need to use this
            property.

            **Do not override this property in your subclass.**

            You also do not need to write this attribute in your component\'s docstring.
    '''
    def __init_subclass__(cls, **kwargs) -> None:
        """Hook called when a subclass is created.

        This validates the __main_method__ property and checks for multiple @main decorators
        within the current class definition. Uses MainMethodResolver for consistent validation logic.

        Note: Multiple inheritance conflicts are intentionally deferred to runtime (get_main())
        to allow class definition to succeed.

        Raises:
            AttributeError: If __main_method__ refers to a non-existent method.
            TypeError: If multiple methods are decorated with @main in the same class.
        """
    @classmethod
    def get_main(cls) -> Callable | None:
        """Return the resolved main coroutine for this Component class.

        This method resolves the main method for the Component class following
        the precedence rules:
        1. Most derived coroutine decorated with `@main`.
        2. Method named by `__main_method__`.
        3. `_run` coroutine as a deprecated fallback.

        Results are cached for performance.

        Returns:
            Callable | None: The coroutine that will be executed by `run()` or
                `None` when no entrypoint can be determined.

        Raises:
            TypeError: If conflicting main methods are inherited from multiple ancestors.
        """
    @property
    def input_params(self) -> type[BaseModel] | None:
        '''Return the Pydantic model describing this component\'s main method input parameters.

        Returns:
            type[BaseModel] | None: The cached model that mirrors the signature of
                the resolved main method, or `None` if no main method can be
                determined.

        Examples:
            ```python
            from pydantic import ValidationError

            component = SomeComponent()
            ParamsModel = component.input_params
            assert ParamsModel.__name__ == "SomeComponentParams"
            fields = list(ParamsModel.model_fields)

            # Validation with valid params
            params = ParamsModel(text="hello")

            # Validation catches missing required fields
            try:
                invalid_params = ParamsModel()  # Missing required \'text\' field
            except ValidationError as e:
                print(f"Validation failed: {e.error_count()} errors")

            # Argument construction
            payload = params.model_dump()
            result = await component.run(**payload)
            ```
        '''
    async def run(self, **kwargs: Any) -> Any:
        """Runs the operations defined for the component.

        This method emits the provided input arguments using an EventEmitter instance if available, executes the
        resolved main method, and emits the resulting output if the EventEmitter is provided.

        The main method is resolved using the following precedence:
        1. Method decorated with @main in the current class.
        2. Method decorated with @main in the nearest ancestor class.
        3. Method named in __main_method__ property.
        4. The _run method (with deprecation warning).

        Args:
            **kwargs (Any): A dictionary of arguments to be processed. May include an `event_emitter`
                key with an EventEmitter instance.

        Returns:
            Any: The result of the resolved main method.

        Raises:
            TypeError: If conflicting main methods are inherited from multiple ancestors.
            AttributeError: If __main_method__ refers to a non-existent method.
        """
    def as_tool(self, name: str | None = None, description: str | None = None, title: str | None = None) -> Tool:
        """Convert the component's main method into a `Tool` instance.

        Example:
            ```python
            from gllm_core.schema import Component, main

            class MyComponent(Component):
                @main
                async def my_method(self, param: str) -> str:
                    return param

            component = MyComponent()
            tool = component.as_tool()
            ```

        Args:
            name (str | None, optional): Identifier for the resulting tool. Defaults to the component class name.
            description (str | None, optional): Summary of the tool's behavior. Defaults to None, in which case the
                main method's docstring is used.
            title (str | None, optional): Optional display title for the tool. Defaults to None, in which case the
                component's class name is used.

        Returns:
            Tool: The tool wrapping the component's main method.

        Raises:
            RuntimeError: If the component does not declare a main method using @main or __main_method__.
        """
    @property
    def run_profile(self) -> RunProfile:
        """Analyzes the `_run` method and retrieves its profile.

        This property method analyzes the `_run` method of the class to generate a `RunProfile` object.
        It also updates the method signatures for methods that fully utilize the arguments.

        Returns:
            RunProfile: The profile of the `_run` method, including method signatures for full-pass argument usages.
        """
