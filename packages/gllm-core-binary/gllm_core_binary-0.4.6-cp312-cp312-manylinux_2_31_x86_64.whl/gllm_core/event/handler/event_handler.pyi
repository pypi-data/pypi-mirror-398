from _typeshed import Incomplete
from abc import ABC, abstractmethod
from gllm_core.constants import EventType as EventType, EventTypeSuffix as EventTypeSuffix
from gllm_core.schema import Event as Event
from gllm_core.utils import LoggerManager as LoggerManager

DEFAULT_COLOR_MAP: Incomplete
DEFAULT_COLOR: str

class BaseEventHandler(ABC):
    """An abstract base class for all event handlers used throughout the Gen AI applications.

    Attributes:
        name (str): The name assigned to the event handler.
        color_map (dict[str, str]): The dictionary that maps certain event types to their
            corresponding colors in Rich format.
    """
    name: Incomplete
    color_map: Incomplete
    def __init__(self, name: str | None = None, color_map: dict[str, str] | None = None) -> None:
        """Initializes a new instance of the BaseEventHandler class.

        Args:
            name (str | None, optional): The name assigned to the event handler. Defaults to None,
                in which case the class name will be used.
            color_map (dict[str, str], optional): The dictionary that maps certain event types to their corresponding
                colors in Rich format. Defaults to None, in which case the default color map will be used.
        """
    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Emits the given event.

        This abstract method must be implemented by subclasses to define how an event is emitted.

        Args:
            event (Event): The event to be emitted.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
    async def close(self) -> None:
        """Closes the event handler.

        By default, this method does nothing. Subclasses can override this method to perform cleanup tasks
        (e.g., closing connections or releasing resources) when needed. Event handlers that do not require
        cleanup can inherit this default behavior without any changes.

        Returns:
            None
        """
