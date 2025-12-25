from abc import ABC, abstractmethod
from gllm_core.schema import Event as Event

class BaseEventHook(ABC):
    """An abstract base class for all event hooks."""
    @abstractmethod
    async def __call__(self, event: Event) -> Event:
        """Applies the hook to the event.

        This abstract method must be implemented by subclasses to define how the hook is applied to the event.

        Args:
            event (Event): The event to apply the hook to.

        Returns:
            Event: The event after the hook is applied.
        """
