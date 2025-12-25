from _typeshed import Incomplete
from gllm_core.event.handler.event_handler import BaseEventHandler as BaseEventHandler
from gllm_core.schema import Event as Event

class ConsoleEventHandler(BaseEventHandler):
    """Defines an event handler class that prints events to the console.

    Attributes:
        name (str): The name assigned to the event handler.
        color_map (dict[str, str]): The dictionary that maps certain event types to their
            corresponding colors in Rich format.
        console (Console): The Rich Console object to use for printing.
    """
    console: Incomplete
    def __init__(self, name: str | None = None, color_map: dict[str, str] | None = None) -> None:
        """Initializes a new instance of the ConsoleEventHandler class.

        Args:
            name (str | None, optional): The name assigned to the event handler. Defaults to None,
                in which case the class name will be used.
            color_map (dict[str, str], optional): The dictionary that maps certain event types to their corresponding
                colors in Rich format. Defaults to None, in which case the default color map will be used.
        """
    async def emit(self, event: Event) -> None:
        """Emits the given event by printing it to the console as a JSON string.

        Args:
            event (Event): The event to be emitted.

        Raises:
            ValueError: If the event type is invalid.
        """
