"""Base domain event class.

Provides a base class for all domain events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    Attributes:
        event_id: Unique identifier for this event instance.
        occurred_at: When the event occurred.
    """

    EVENT_TYPE: ClassVar[str] = "DomainEvent"

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def get_event_type(cls) -> str:
        """Get the event type name.

        Returns:
            The event type name.
        """
        return cls.EVENT_TYPE
