from _typeshed import Incomplete
from gllm_core.utils.logger_manager import LoggerManager as LoggerManager
from typing import Callable

class MainMethodResolver:
    """Resolves the main entrypoint method for Component classes.

    This resolver implements the precedence rules for determining which method
    should be used as the main entrypoint:
    1. Method decorated with @main in the most derived class.
    2. Method named by __main_method__ property.
    3. _run method (with deprecation warning).

    Attributes:
        cls (type): The Component class to resolve the main method for.
    """
    cls: Incomplete
    def __init__(self, component_class: type) -> None:
        """Initialize the resolver with a Component class.

        Args:
            component_class (type): The Component class to resolve the main method for.
        """
    @staticmethod
    def validate_class(component_class: type) -> None:
        """Validate main method configuration at class definition time.

        This performs early validation that can be done when a Component subclass
        is defined, before any instances are created or methods are called.

        Validations performed:
        1. Check that __main_method__ property points to an existing method
        2. Check that only one @main decorator is used within the same class

        Note: Multiple inheritance conflicts are intentionally NOT checked here,
        as they are deferred to runtime (get_main()) to allow class definition
        to succeed.

        Args:
            component_class (type): The Component class to validate.

        Raises:
            AttributeError: If __main_method__ refers to a non-existent method.
            TypeError: If multiple methods are decorated with @main in the same class.
        """
    def resolve(self) -> Callable | None:
        """Resolve the main method following precedence rules.

        Returns:
            Callable | None: The resolved main method, or None if not found.

        Raises:
            TypeError: If conflicting main methods are inherited from multiple ancestors.
        """
