"""Calendar service for Sonnerrise Calendar."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import and_

from sonnerrise_calendar.schemas import (
    CalendarDay,
    CalendarEvent,
    EventList,
    MonthView,
    UpcomingEvent,
    WeekView,
)

if TYPE_CHECKING:
    from sonnerrise_core.database import DatabasePlugin


class CalendarService:
    """Service for calendar views and event management.

    Provides read-only calendar views aggregating events from tracks,
    with the ability to toggle event enabled status.
    """

    def __init__(self, db: DatabasePlugin) -> None:
        """Initialize the calendar service.

        Args:
            db: Database plugin instance.
        """
        self._db = db

    def _get_events_for_range(
        self,
        start_date: date,
        end_date: date,
        include_disabled: bool = True,
    ) -> list[CalendarEvent]:
        """Get all events within a date range.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).
            include_disabled: Whether to include disabled events.

        Returns:
            List of calendar events.
        """
        from sonnerrise_tracks.models import Track, TrackEvent

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        with self._db.session() as session:
            query = (
                session.query(TrackEvent)
                .join(Track)
                .filter(
                    and_(
                        TrackEvent.datetime >= start_datetime,
                        TrackEvent.datetime <= end_datetime,
                    )
                )
            )

            if not include_disabled:
                query = query.filter(TrackEvent.enabled == True)

            query = query.order_by(TrackEvent.datetime)
            events = query.all()

            return [
                CalendarEvent(
                    event_id=e.id,
                    track_id=e.track_id,
                    track_title=e.track.title,
                    datetime=e.datetime,
                    description=e.description,
                    enabled=e.enabled,
                )
                for e in events
            ]

    def get_day_view(
        self,
        day: date,
        include_disabled: bool = True,
    ) -> CalendarDay:
        """Get calendar view for a single day.

        Args:
            day: The date to view.
            include_disabled: Whether to include disabled events.

        Returns:
            CalendarDay with events.
        """
        events = self._get_events_for_range(day, day, include_disabled)
        return CalendarDay(date=day, events=events)

    def get_week_view(
        self,
        reference_date: date | None = None,
        include_disabled: bool = True,
    ) -> WeekView:
        """Get calendar view for a week.

        Args:
            reference_date: Any date within the desired week. Defaults to today.
            include_disabled: Whether to include disabled events.

        Returns:
            WeekView with days and events.
        """
        if reference_date is None:
            reference_date = date.today()

        # Find Monday of the week
        days_since_monday = reference_date.weekday()
        start_date = reference_date - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=6)

        # Get all events for the week
        events = self._get_events_for_range(start_date, end_date, include_disabled)

        # Group events by date
        events_by_date: dict[date, list[CalendarEvent]] = {}
        for event in events:
            event_date = event.datetime.date()
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        # Build days
        days = []
        current = start_date
        while current <= end_date:
            day_events = events_by_date.get(current, [])
            days.append(CalendarDay(date=current, events=day_events))
            current += timedelta(days=1)

        return WeekView(
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

    def get_month_view(
        self,
        year: int | None = None,
        month: int | None = None,
        include_disabled: bool = True,
    ) -> MonthView:
        """Get calendar view for a month.

        Args:
            year: Year. Defaults to current year.
            month: Month (1-12). Defaults to current month.
            include_disabled: Whether to include disabled events.

        Returns:
            MonthView with weeks and events.
        """
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Extend to full weeks (Monday to Sunday)
        start_date = first_day - timedelta(days=first_day.weekday())
        end_date = last_day + timedelta(days=6 - last_day.weekday())

        # Get all events for the range
        events = self._get_events_for_range(start_date, end_date, include_disabled)

        # Group events by date
        events_by_date: dict[date, list[CalendarEvent]] = {}
        for event in events:
            event_date = event.datetime.date()
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        # Build weeks
        weeks = []
        current = start_date
        while current <= end_date:
            week = []
            for _ in range(7):
                day_events = events_by_date.get(current, [])
                week.append(CalendarDay(date=current, events=day_events))
                current += timedelta(days=1)
            weeks.append(week)

        return MonthView(
            year=year,
            month=month,
            weeks=weeks,
        )

    def get_upcoming_events(
        self,
        days: int = 7,
        include_disabled: bool = False,
        limit: int | None = None,
    ) -> EventList:
        """Get upcoming events within a number of days.

        Args:
            days: Number of days to look ahead.
            include_disabled: Whether to include disabled events.
            limit: Maximum number of events to return. None for no limit.

        Returns:
            EventList with upcoming events.
        """
        from sonnerrise_tracks.models import Track, TrackEvent

        now = datetime.now()
        end_datetime = now + timedelta(days=days)

        with self._db.session() as session:
            query = (
                session.query(TrackEvent)
                .join(Track)
                .filter(
                    and_(
                        TrackEvent.datetime >= now,
                        TrackEvent.datetime <= end_datetime,
                    )
                )
            )

            if not include_disabled:
                query = query.filter(TrackEvent.enabled == True)

            query = query.order_by(TrackEvent.datetime)

            if limit is not None:
                query = query.limit(limit)

            events = query.all()

            upcoming = [
                UpcomingEvent(
                    event_id=e.id,
                    track_id=e.track_id,
                    track_title=e.track.title,
                    track_album=e.track.album,
                    datetime=e.datetime,
                    description=e.description,
                    enabled=e.enabled,
                    days_until=max(0, (e.datetime.date() - date.today()).days),
                )
                for e in events
            ]

            return EventList(
                events=upcoming,
                total=len(upcoming),
                days_range=days,
            )

    def get_today_events(
        self,
        include_disabled: bool = True,
    ) -> list[CalendarEvent]:
        """Get all events for today.

        Args:
            include_disabled: Whether to include disabled events.

        Returns:
            List of today's events.
        """
        today = date.today()
        return self._get_events_for_range(today, today, include_disabled)

    def toggle_event(self, track_id: int, event_id: int) -> bool:
        """Toggle an event's enabled status.

        Args:
            track_id: The track ID.
            event_id: The event ID.

        Returns:
            The new enabled status.

        Raises:
            ValueError: If event not found.
        """
        from sonnerrise_tracks.models import TrackEvent

        with self._db.session() as session:
            event = (
                session.query(TrackEvent)
                .filter(
                    TrackEvent.id == event_id,
                    TrackEvent.track_id == track_id,
                )
                .first()
            )

            if event is None:
                raise ValueError(f"Event {event_id} not found for track {track_id}")

            event.enabled = not event.enabled
            session.commit()
            return event.enabled

    def get_event_count_by_month(
        self,
        year: int,
        include_disabled: bool = False,
    ) -> dict[int, int]:
        """Get event counts by month for a year.

        Args:
            year: The year to analyze.
            include_disabled: Whether to include disabled events.

        Returns:
            Dictionary mapping month (1-12) to event count.
        """
        from sonnerrise_tracks.models import TrackEvent

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        with self._db.session() as session:
            query = session.query(TrackEvent).filter(
                and_(
                    TrackEvent.datetime >= start_date,
                    TrackEvent.datetime <= end_date,
                )
            )

            if not include_disabled:
                query = query.filter(TrackEvent.enabled == True)

            events = query.all()

            # Count by month (must be done inside session)
            counts: dict[int, int] = {m: 0 for m in range(1, 13)}
            for event in events:
                counts[event.datetime.month] += 1

            return counts

    def get_tracks_with_upcoming_events(
        self,
        days: int = 7,
    ) -> list[dict]:
        """Get tracks that have upcoming events.

        Args:
            days: Number of days to look ahead.

        Returns:
            List of track info with event counts.
        """
        from sonnerrise_tracks.models import Track, TrackEvent

        now = datetime.now()
        end_datetime = now + timedelta(days=days)

        with self._db.session() as session:
            tracks = (
                session.query(Track)
                .join(TrackEvent)
                .filter(
                    and_(
                        TrackEvent.datetime >= now,
                        TrackEvent.datetime <= end_datetime,
                        TrackEvent.enabled == True,
                    )
                )
                .distinct()
                .all()
            )

            result = []
            for track in tracks:
                upcoming = [
                    e for e in track.events
                    if e.enabled and e.datetime >= now and e.datetime <= end_datetime
                ]
                result.append({
                    "track_id": track.id,
                    "title": track.title,
                    "album": track.album,
                    "upcoming_event_count": len(upcoming),
                    "next_event": min(upcoming, key=lambda e: e.datetime) if upcoming else None,
                })

            return sorted(result, key=lambda x: x["next_event"].datetime if x["next_event"] else now)
