"""Calendar views for Sonnerrise web interface."""

from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from sonnerrise_calendar import CalendarService
from sonnerrise_tracks import TrackEvent
from sonnerrise_web.app import get_db, get_session

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/")
def index():
    """Show calendar overview with weekly/monthly views."""
    db = get_db()
    calendar_service = CalendarService(db)

    # Get view type
    view_type = request.args.get("view", "month")

    # Get date parameters
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    week = request.args.get("week", type=int)

    today = date.today()

    if view_type == "week":
        if year and week:
            # Calculate the start of the specified week
            jan1 = date(year, 1, 1)
            days_to_monday = (7 - jan1.weekday()) % 7
            first_monday = jan1 + timedelta(days=days_to_monday)
            if jan1.weekday() == 0:  # If Jan 1 is Monday
                first_monday = jan1
            week_start = first_monday + timedelta(weeks=week - 1)
        else:
            # Current week
            year = today.year
            week_start = today - timedelta(days=today.weekday())
            # Calculate ISO week number
            week = week_start.isocalendar()[1]

        week_view = calendar_service.get_week_view(week_start)

        # Calculate previous and next week
        prev_week_start = week_start - timedelta(weeks=1)
        next_week_start = week_start + timedelta(weeks=1)

        return render_template(
            "calendar/week.html",
            week_view=week_view,
            week_start=week_start,
            year=year,
            week=week,
            prev_year=prev_week_start.year,
            prev_week=prev_week_start.isocalendar()[1],
            next_year=next_week_start.year,
            next_week=next_week_start.isocalendar()[1],
        )
    else:
        # Month view
        if year and month:
            pass
        else:
            year = today.year
            month = today.month

        month_view = calendar_service.get_month_view(year, month)

        # Calculate previous and next month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        # Get upcoming events
        upcoming = calendar_service.get_upcoming_events(limit=10)

        return render_template(
            "calendar/month.html",
            month_view=month_view,
            year=year,
            month=month,
            prev_year=prev_year,
            prev_month=prev_month,
            next_year=next_year,
            next_month=next_month,
            upcoming=upcoming,
        )


@calendar_bp.route("/event/<int:event_id>/toggle", methods=["POST"])
def toggle_event(event_id: int):
    """Toggle an event's enabled state."""
    session = get_session()
    event = session.query(TrackEvent).get(event_id)

    if event:
        event.is_enabled = not event.is_enabled
        session.commit()
        flash(f"Event {'enabled' if event.is_enabled else 'disabled'}.", "success")
    else:
        flash("Event not found.", "danger")

    # Redirect back to referring page
    return redirect(request.referrer or url_for("calendar.index"))
