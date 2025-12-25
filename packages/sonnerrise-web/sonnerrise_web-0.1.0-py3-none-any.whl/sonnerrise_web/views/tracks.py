"""Tracks views for Sonnerrise web interface."""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from sonnerrise_definitions import Definition
from sonnerrise_tracks import Track, TrackEvent, TrackLink, TrackRepository
from sonnerrise_web.app import get_session
from sonnerrise_web.forms import TrackEventForm, TrackForm

tracks_bp = Blueprint("tracks", __name__)


@tracks_bp.route("/")
def list():
    """List all tracks with pagination and filtering."""
    session = get_session()

    # Get filter parameters
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Build query
    query = session.query(Track)

    if search:
        query = query.filter(
            (Track.title.ilike(f"%{search}%"))
            | (Track.album.ilike(f"%{search}%"))
        )

    # Get total count
    total = query.count()

    # Paginate
    tracks = (
        query.order_by(Track.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "tracks/list.html",
        tracks=tracks,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@tracks_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new track."""
    session = get_session()
    form = TrackForm()

    # Populate definition choices
    definitions = session.query(Definition).order_by(Definition.title).all()
    form.definition_id.choices = [("", "None")] + [
        (str(d.id), d.title) for d in definitions
    ]

    if form.validate_on_submit():
        track = Track(
            title=form.title.data,
            album=form.album.data or None,
            definition_id=form.definition_id.data,
            cover_art_url=form.cover_art_url.data or None,
            lyrics=form.lyrics.data or None,
            comments=form.comments.data or None,
        )
        session.add(track)
        session.commit()

        flash("Track created successfully.", "success")
        return redirect(url_for("tracks.edit", id=track.id))

    return render_template("tracks/form.html", form=form, title="New Track")


@tracks_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id: int):
    """Edit an existing track."""
    session = get_session()
    track = session.query(Track).get(id)

    if not track:
        flash("Track not found.", "danger")
        return redirect(url_for("tracks.list"))

    form = TrackForm(obj=track)
    event_form = TrackEventForm()

    # Populate definition choices
    definitions = session.query(Definition).order_by(Definition.title).all()
    form.definition_id.choices = [("", "None")] + [
        (str(d.id), d.title) for d in definitions
    ]

    if form.validate_on_submit():
        track.title = form.title.data
        track.album = form.album.data or None
        track.definition_id = form.definition_id.data
        track.cover_art_url = form.cover_art_url.data or None
        track.lyrics = form.lyrics.data or None
        track.comments = form.comments.data or None
        session.commit()

        flash("Track updated successfully.", "success")
        return redirect(url_for("tracks.edit", id=id))

    # Get links and events
    links = session.query(TrackLink).filter_by(track_id=id).all()
    events = session.query(TrackEvent).filter_by(track_id=id).order_by(TrackEvent.event_date).all()

    return render_template(
        "tracks/form.html",
        form=form,
        event_form=event_form,
        title="Edit Track",
        track=track,
        links=links,
        events=events,
    )


@tracks_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id: int):
    """Delete a track."""
    session = get_session()
    track = session.query(Track).get(id)

    if not track:
        flash("Track not found.", "danger")
        return redirect(url_for("tracks.list"))

    # Delete associated links and events
    session.query(TrackLink).filter_by(track_id=id).delete()
    session.query(TrackEvent).filter_by(track_id=id).delete()

    session.delete(track)
    session.commit()

    flash("Track deleted successfully.", "success")
    return redirect(url_for("tracks.list"))


@tracks_bp.route("/<int:id>/links/add", methods=["POST"])
def add_link(id: int):
    """Add a link to a track."""
    session = get_session()
    track = session.query(Track).get(id)

    if not track:
        flash("Track not found.", "danger")
        return redirect(url_for("tracks.list"))

    url = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()

    if url:
        link = TrackLink(
            track_id=id,
            url=url,
            title=title or None,
        )
        session.add(link)
        session.commit()
        flash("Link added.", "success")
    else:
        flash("URL is required.", "danger")

    return redirect(url_for("tracks.edit", id=id))


@tracks_bp.route("/<int:id>/links/<int:link_id>/delete", methods=["POST"])
def delete_link(id: int, link_id: int):
    """Delete a link from a track."""
    session = get_session()
    link = session.query(TrackLink).filter_by(id=link_id, track_id=id).first()

    if link:
        session.delete(link)
        session.commit()
        flash("Link deleted.", "success")
    else:
        flash("Link not found.", "danger")

    return redirect(url_for("tracks.edit", id=id))


@tracks_bp.route("/<int:id>/events/add", methods=["POST"])
def add_event(id: int):
    """Add an event to a track."""
    session = get_session()
    track = session.query(Track).get(id)

    if not track:
        flash("Track not found.", "danger")
        return redirect(url_for("tracks.list"))

    event_date_str = request.form.get("event_date", "").strip()
    description = request.form.get("description", "").strip()

    if event_date_str and description:
        try:
            event_date = datetime.fromisoformat(event_date_str)
            event = TrackEvent(
                track_id=id,
                event_date=event_date,
                description=description,
                is_enabled=True,
            )
            session.add(event)
            session.commit()
            flash("Event added.", "success")
        except ValueError:
            flash("Invalid date format.", "danger")
    else:
        flash("Date and description are required.", "danger")

    return redirect(url_for("tracks.edit", id=id))


@tracks_bp.route("/<int:id>/events/<int:event_id>/toggle", methods=["POST"])
def toggle_event(id: int, event_id: int):
    """Toggle an event's enabled state."""
    session = get_session()
    event = session.query(TrackEvent).filter_by(id=event_id, track_id=id).first()

    if event:
        event.is_enabled = not event.is_enabled
        session.commit()
        flash(f"Event {'enabled' if event.is_enabled else 'disabled'}.", "success")
    else:
        flash("Event not found.", "danger")

    return redirect(url_for("tracks.edit", id=id))


@tracks_bp.route("/<int:id>/events/<int:event_id>/delete", methods=["POST"])
def delete_event(id: int, event_id: int):
    """Delete an event from a track."""
    session = get_session()
    event = session.query(TrackEvent).filter_by(id=event_id, track_id=id).first()

    if event:
        session.delete(event)
        session.commit()
        flash("Event deleted.", "success")
    else:
        flash("Event not found.", "danger")

    return redirect(url_for("tracks.edit", id=id))
