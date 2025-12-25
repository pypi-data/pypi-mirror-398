"""Sonnerrise Calendar - Track events calendar view module."""

from sonnerrise_calendar.schemas import (
    CalendarDay,
    CalendarEvent,
    EventList,
    MonthView,
    UpcomingEvent,
    WeekView,
)
from sonnerrise_calendar.service import CalendarService

__version__ = "0.1.0"

__all__ = [
    # Service
    "CalendarService",
    # Schemas
    "CalendarDay",
    "CalendarEvent",
    "EventList",
    "MonthView",
    "UpcomingEvent",
    "WeekView",
    # Version
    "__version__",
]
