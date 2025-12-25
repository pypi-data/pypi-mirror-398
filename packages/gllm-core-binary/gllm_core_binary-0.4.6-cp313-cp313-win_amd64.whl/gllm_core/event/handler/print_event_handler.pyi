from _typeshed import Incomplete
from gllm_core.constants import EventType as EventType, EventTypeSuffix as EventTypeSuffix
from gllm_core.event.handler.event_handler import BaseEventHandler as BaseEventHandler
from gllm_core.schema import Event as Event

class PrintEventHandler(BaseEventHandler):
    """An event handler that prints the event with human readable format.

    Attributes:
        name (str): The name assigned to the event handler.
        padding_char (str): The character to use for padding.
        color_map (dict[str, str]): The dictionary that maps certain event types to their
            corresponding colors in Rich format.
        console (Console): The Rich Console object to use for printing.
    """
    padding_char: Incomplete
    console: Incomplete
    def __init__(self, name: str | None = None, color_map: dict[str, str] | None = None, padding_char: str = '=') -> None:
        '''Initializes a new instance of the PrintEventHandler class.

        Args:
            name (str | None, optional): The name assigned to the event handler. Defaults to None,
                in which case the class name will be used.
            color_map (dict[str, str], optional): The dictionary that maps certain event types to their corresponding
                colors in Rich format. Defaults to None, in which case the default color map will be used.
            padding_char (str, optional): The character to use for padding. Defaults to "=".
        '''
    async def emit(self, event: Event) -> None:
        """Emits the given event.

        Args:
            event (Event): The event to be emitted.
        """
