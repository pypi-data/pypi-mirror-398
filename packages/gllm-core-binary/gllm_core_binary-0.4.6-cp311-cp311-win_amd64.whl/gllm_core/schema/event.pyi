from datetime import datetime
from gllm_core.constants import EventLevel as EventLevel, EventType as EventType
from pydantic import BaseModel
from typing import Any

class Event(BaseModel):
    """A data class to store an event attributes.

    Attributes:
        id (str): The ID of the event. Defaults to None.
        value (str | dict[str, Any]): The value of the event. Defaults to an empty string.
        level (EventLevel): The severity level of the event. Defaults to EventLevel.INFO.
        type (str): The type of the event. Defaults to EventType.RESPONSE.
        timestamp (datetime): The timestamp of the event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the event. Defaults to an empty dictionary.
    """
    id: str | None
    value: str | dict[str, Any]
    level: EventLevel
    type: str
    timestamp: datetime
    metadata: dict[str, Any]
    def serialize_level(self, level: EventLevel) -> str:
        """Serializes an EventLevel object into its string representation.

        This method serializes the given EventLevel object by returning its name as a string.

        Args:
            level (EventLevel): The EventLevel object to be serialized.

        Returns:
            str: The name of the EventLevel object.
        """
