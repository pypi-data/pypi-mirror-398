from gllm_core.event.hook.event_hook import BaseEventHook as BaseEventHook
from gllm_core.schema import Event as Event

class JSONStringifyEventHook(BaseEventHook):
    """An event hook to JSON stringify the event value."""
    async def __call__(self, event: Event) -> Event:
        """Applies the hook to the event.

        This method will convert the event value to a JSON string if it is a dictionary.

        Args:
            event (Event): The event to apply the hook to.

        Returns:
            Event: The event after the hook is applied.
        """
