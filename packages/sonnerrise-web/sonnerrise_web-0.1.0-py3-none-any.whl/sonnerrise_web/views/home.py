"""Home view for Sonnerrise web interface."""

from flask import Blueprint, render_template

from sonnerrise_web.app import get_db, get_session

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    """Render home page with dashboard overview."""
    session = get_session()

    # Get counts for dashboard
    from sonnerrise_definitions import Definition
    from sonnerrise_personas import Persona
    from sonnerrise_promo import Promo
    from sonnerrise_tracks import Track

    stats = {
        "personas": session.query(Persona).count(),
        "definitions": session.query(Definition).count(),
        "tracks": session.query(Track).count(),
        "promos": session.query(Promo).count(),
    }

    # Get upcoming events
    from sonnerrise_calendar import CalendarService

    db = get_db()
    calendar_service = CalendarService(db)
    upcoming = calendar_service.get_upcoming_events(limit=5)

    return render_template("home/index.html", stats=stats, upcoming=upcoming)
