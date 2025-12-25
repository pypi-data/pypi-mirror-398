"""Command-line interface for sonnerrise-calendar."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from sonnerrise_calendar import __version__
from sonnerrise_calendar.service import CalendarService


def get_db():
    """Get database connection from config."""
    from sonnerrise_core import get_database, load_config

    config = load_config()
    return get_database(config)


def parse_date(s: str) -> date:
    """Parse date from string."""
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {s}. Use YYYY-MM-DD")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-calendar",
        description="Sonnerrise Calendar - View track events calendar",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # today command
    today_parser = subparsers.add_parser("today", help="Show today's events")
    today_parser.add_argument(
        "--all", "-a", action="store_true", help="Include disabled events"
    )

    # week command
    week_parser = subparsers.add_parser("week", help="Show week view")
    week_parser.add_argument(
        "--date", "-d", type=str, help="Any date in the week (YYYY-MM-DD)"
    )
    week_parser.add_argument(
        "--all", "-a", action="store_true", help="Include disabled events"
    )

    # month command
    month_parser = subparsers.add_parser("month", help="Show month view")
    month_parser.add_argument("--year", "-y", type=int, help="Year")
    month_parser.add_argument("--month", "-m", type=int, help="Month (1-12)")
    month_parser.add_argument(
        "--all", "-a", action="store_true", help="Include disabled events"
    )

    # upcoming command
    upcoming_parser = subparsers.add_parser("upcoming", help="Show upcoming events")
    upcoming_parser.add_argument(
        "--days", "-d", type=int, default=7, help="Days to look ahead"
    )
    upcoming_parser.add_argument(
        "--all", "-a", action="store_true", help="Include disabled events"
    )

    # toggle command
    toggle_parser = subparsers.add_parser("toggle", help="Toggle event enabled status")
    toggle_parser.add_argument("track_id", type=int, help="Track ID")
    toggle_parser.add_argument("event_id", type=int, help="Event ID")

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Show year summary")
    summary_parser.add_argument("--year", "-y", type=int, help="Year (default: current)")

    return parser


def cmd_today(args: argparse.Namespace) -> int:
    """Show today's events."""
    db = get_db()
    calendar = CalendarService(db)

    events = calendar.get_today_events(include_disabled=args.all)

    if not events:
        print("No events today.")
        return 0

    print(f"Today's Events ({date.today().strftime('%A, %B %d, %Y')}):\n")
    print(f"{'Time':<8} {'Track':<30} {'Event':<35} {'Status':<10}")
    print("-" * 83)

    for event in events:
        status = "enabled" if event.enabled else "DISABLED"
        track = event.track_title[:28] if len(event.track_title) > 28 else event.track_title
        desc = event.description[:33] if len(event.description) > 33 else event.description
        print(f"{event.time_str:<8} {track:<30} {desc:<35} {status:<10}")

    return 0


def cmd_week(args: argparse.Namespace) -> int:
    """Show week view."""
    db = get_db()
    calendar = CalendarService(db)

    ref_date = None
    if args.date:
        try:
            ref_date = parse_date(args.date)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    week = calendar.get_week_view(ref_date, include_disabled=args.all)

    print(f"Week {week.week_number}, {week.year}")
    print(f"({week.start_date.strftime('%b %d')} - {week.end_date.strftime('%b %d')})")
    print(f"Total events: {week.total_events}\n")

    for day in week.days:
        day_marker = " *" if day.is_today else ""
        print(f"{day.day_name[:3]} {day.date_str}{day_marker}")

        if day.events:
            for event in day.events:
                status = "" if event.enabled else " [DISABLED]"
                print(f"    {event.time_str} - {event.track_title}: {event.description}{status}")
        else:
            print("    (no events)")
        print()

    return 0


def cmd_month(args: argparse.Namespace) -> int:
    """Show month view."""
    db = get_db()
    calendar = CalendarService(db)

    month = calendar.get_month_view(args.year, args.month, include_disabled=args.all)

    print(f"{month.month_name} {month.year}")
    print(f"Total events: {month.total_events}")
    print(f"Days with events: {month.days_with_events}\n")

    # Print header
    print("Mon       Tue       Wed       Thu       Fri       Sat       Sun")
    print("-" * 69)

    for week in month.weeks:
        # First line: dates
        date_line = ""
        for day in week:
            marker = "*" if day.is_today else " "
            in_month = day.date.month == month.month
            if in_month:
                date_line += f"{day.date.day:2d}{marker}({day.event_count})   "
            else:
                date_line += "          "
        print(date_line)

        # Second line: first event (if any)
        event_line = ""
        for day in week:
            if day.events and day.date.month == month.month:
                first = day.events[0]
                desc = first.description[:7] if len(first.description) > 7 else first.description
                event_line += f"{desc:<10}"
            else:
                event_line += "          "
        if event_line.strip():
            print(event_line)
        print()

    return 0


def cmd_upcoming(args: argparse.Namespace) -> int:
    """Show upcoming events."""
    db = get_db()
    calendar = CalendarService(db)

    event_list = calendar.get_upcoming_events(
        days=args.days,
        include_disabled=args.all,
    )

    if not event_list.events:
        print(f"No upcoming events in the next {args.days} days.")
        return 0

    print(f"Upcoming Events (next {args.days} days): {event_list.total} total")
    if event_list.has_urgent:
        print("⚠ You have events today or tomorrow!\n")
    else:
        print()

    print(f"{'Days':<6} {'Date':<12} {'Time':<6} {'Track':<25} {'Event':<30}")
    print("-" * 79)

    for event in event_list.events:
        days_str = "TODAY" if event.days_until == 0 else f"{event.days_until}d"
        date_str = event.datetime.strftime("%b %d")
        time_str = event.datetime.strftime("%H:%M")
        track = event.track_title[:23] if len(event.track_title) > 23 else event.track_title
        desc = event.description[:28] if len(event.description) > 28 else event.description

        print(f"{days_str:<6} {date_str:<12} {time_str:<6} {track:<25} {desc:<30}")

    return 0


def cmd_toggle(args: argparse.Namespace) -> int:
    """Toggle event enabled status."""
    db = get_db()
    calendar = CalendarService(db)

    try:
        new_status = calendar.toggle_event(args.track_id, args.event_id)
        status_str = "enabled" if new_status else "disabled"
        print(f"Event {args.event_id} is now {status_str}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_summary(args: argparse.Namespace) -> int:
    """Show year summary."""
    db = get_db()
    calendar = CalendarService(db)

    year = args.year if args.year else date.today().year
    counts = calendar.get_event_count_by_month(year, include_disabled=False)

    print(f"Event Summary for {year}\n")

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    total = sum(counts.values())

    for month_num, count in counts.items():
        bar = "█" * count if count > 0 else ""
        print(f"{month_names[month_num-1]}: {count:3d} {bar}")

    print(f"\nTotal: {total} events")

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        # Default to showing upcoming events
        args.command = "upcoming"
        args.days = 7
        args.all = False

    commands = {
        "today": cmd_today,
        "week": cmd_week,
        "month": cmd_month,
        "upcoming": cmd_upcoming,
        "toggle": cmd_toggle,
        "summary": cmd_summary,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
