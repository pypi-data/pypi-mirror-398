"""Pydantic schemas for Sonnerrise Calendar."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class CalendarEvent(BaseModel):
    """An event in the calendar view."""

    event_id: int
    track_id: int
    track_title: str
    datetime: datetime
    description: str
    enabled: bool

    @computed_field
    @property
    def days_until(self) -> int:
        """Days until (positive) or since (negative) the event."""
        delta = self.datetime.date() - date.today()
        return delta.days

    @computed_field
    @property
    def is_past(self) -> bool:
        """Whether the event is in the past."""
        return self.datetime < datetime.now()

    @computed_field
    @property
    def is_today(self) -> bool:
        """Whether the event is today."""
        return self.datetime.date() == date.today()

    @computed_field
    @property
    def time_str(self) -> str:
        """Formatted time string."""
        return self.datetime.strftime("%H:%M")

    @computed_field
    @property
    def date_str(self) -> str:
        """Formatted date string."""
        return self.datetime.strftime("%Y-%m-%d")

    @computed_field
    @property
    def datetime_str(self) -> str:
        """Formatted datetime string."""
        return self.datetime.strftime("%Y-%m-%d %H:%M")


class CalendarDay(BaseModel):
    """A single day in the calendar."""

    date: date
    events: list[CalendarEvent] = Field(default_factory=list)

    @computed_field
    @property
    def is_today(self) -> bool:
        """Whether this day is today."""
        return self.date == date.today()

    @computed_field
    @property
    def is_past(self) -> bool:
        """Whether this day is in the past."""
        return self.date < date.today()

    @computed_field
    @property
    def day_name(self) -> str:
        """Day of the week name."""
        return self.date.strftime("%A")

    @computed_field
    @property
    def day_short(self) -> str:
        """Short day name."""
        return self.date.strftime("%a")

    @computed_field
    @property
    def date_str(self) -> str:
        """Formatted date string."""
        return self.date.strftime("%Y-%m-%d")

    @computed_field
    @property
    def event_count(self) -> int:
        """Number of events on this day."""
        return len(self.events)

    @computed_field
    @property
    def enabled_event_count(self) -> int:
        """Number of enabled events on this day."""
        return sum(1 for e in self.events if e.enabled)


class WeekView(BaseModel):
    """A week view of the calendar."""

    start_date: date
    end_date: date
    days: list[CalendarDay] = Field(default_factory=list)

    @computed_field
    @property
    def total_events(self) -> int:
        """Total events in the week."""
        return sum(day.event_count for day in self.days)

    @computed_field
    @property
    def week_number(self) -> int:
        """ISO week number."""
        return self.start_date.isocalendar()[1]

    @computed_field
    @property
    def year(self) -> int:
        """Year of the week."""
        return self.start_date.year


class MonthView(BaseModel):
    """A month view of the calendar."""

    year: int
    month: int
    weeks: list[list[CalendarDay]] = Field(default_factory=list)

    @computed_field
    @property
    def month_name(self) -> str:
        """Name of the month."""
        return date(self.year, self.month, 1).strftime("%B")

    @computed_field
    @property
    def total_events(self) -> int:
        """Total events in the month."""
        return sum(
            day.event_count
            for week in self.weeks
            for day in week
        )

    @computed_field
    @property
    def days_with_events(self) -> int:
        """Number of days with at least one event."""
        return sum(
            1 for week in self.weeks
            for day in week
            if day.event_count > 0
        )


class UpcomingEvent(BaseModel):
    """An upcoming event with additional context."""

    event_id: int
    track_id: int
    track_title: str
    track_album: str | None
    datetime: datetime
    description: str
    enabled: bool
    days_until: int

    @computed_field
    @property
    def urgency(self) -> str:
        """Urgency level based on days until event."""
        if self.days_until <= 0:
            return "now"
        elif self.days_until == 1:
            return "tomorrow"
        elif self.days_until <= 3:
            return "soon"
        elif self.days_until <= 7:
            return "this_week"
        else:
            return "later"

    @computed_field
    @property
    def datetime_str(self) -> str:
        """Formatted datetime string."""
        return self.datetime.strftime("%Y-%m-%d %H:%M")


class EventList(BaseModel):
    """A list of events with summary."""

    events: list[UpcomingEvent] = Field(default_factory=list)
    total: int = 0
    days_range: int = 7

    @computed_field
    @property
    def by_urgency(self) -> dict[str, list[UpcomingEvent]]:
        """Events grouped by urgency."""
        result: dict[str, list[UpcomingEvent]] = {
            "now": [],
            "tomorrow": [],
            "soon": [],
            "this_week": [],
            "later": [],
        }
        for event in self.events:
            result[event.urgency].append(event)
        return result

    @computed_field
    @property
    def has_urgent(self) -> bool:
        """Whether there are urgent events (today or tomorrow)."""
        return any(e.days_until <= 1 for e in self.events)
