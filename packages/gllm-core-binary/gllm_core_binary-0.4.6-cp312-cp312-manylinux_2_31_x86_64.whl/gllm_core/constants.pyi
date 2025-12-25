from enum import IntEnum, StrEnum

class EventLevel(IntEnum):
    """Defines event levels for the event emitter module."""
    TRACE: int
    DEBUG: int
    INFO: int
    WARN: int
    ERROR: int
    FATAL: int

class EventType(StrEnum):
    """Defines event types for the event emitter module."""
    ACTIVITY: str
    CODE: str
    REFERENCE: str
    RESPONSE: str
    STATUS: str
    THINKING: str

class EventTypeSuffix(StrEnum):
    """Defines suffixes for block based event types."""
    START: str
    END: str

class DefaultChunkMetadata:
    """Defines constants for default chunk metadata keys."""
    CHUNK_ID: str
    PREV_CHUNK_ID: str
    NEXT_CHUNK_ID: str

class LogMode(StrEnum):
    """Defines supported log modes for the SDK logging system."""
    TEXT: str
    SIMPLE: str
    JSON: str
