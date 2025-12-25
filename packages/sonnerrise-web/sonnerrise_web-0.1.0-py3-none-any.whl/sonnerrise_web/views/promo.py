"""Promo views for Sonnerrise web interface."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from sonnerrise_promo import Promo, PromoLink, PromoRepository
from sonnerrise_tracks import Track
from sonnerrise_web.app import get_session
from sonnerrise_web.forms import PromoForm

promo_bp = Blueprint("promo", __name__)


@promo_bp.route("/")
def list():
    """List all promos with pagination and filtering."""
    session = get_session()

    # Get filter parameters
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Build query with join to track
    query = session.query(Promo).join(Track)

    if search:
        query = query.filter(Track.title.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Paginate
    promos = (
        query.order_by(Promo.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "promo/list.html",
        promos=promos,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@promo_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new promo."""
    session = get_session()
    form = PromoForm()

    # Get pre-selected track if provided
    track_id = request.args.get("track_id", type=int)

    # Populate track choices - only tracks without promos
    existing_promo_track_ids = [p.track_id for p in session.query(Promo).all()]
    tracks = (
        session.query(Track)
        .filter(~Track.id.in_(existing_promo_track_ids) if existing_promo_track_ids else True)
        .order_by(Track.title)
        .all()
    )

    # If a specific track is requested, include it even if it has a promo
    if track_id:
        selected_track = session.query(Track).get(track_id)
        if selected_track and selected_track not in tracks:
            tracks.insert(0, selected_track)

    form.track_id.choices = [(str(t.id), t.title) for t in tracks]

    if track_id and request.method == "GET":
        form.track_id.data = str(track_id)

    if form.validate_on_submit():
        promo = Promo(
            track_id=int(form.track_id.data),
            track_art_definition=form.track_art_definition.data or None,
            canvas_definition=form.canvas_definition.data or None,
            pitch=form.pitch.data or None,
            summary=form.summary.data or None,
        )
        session.add(promo)
        session.commit()

        flash("Promotion created successfully.", "success")
        return redirect(url_for("promo.edit", id=promo.id))

    return render_template("promo/form.html", form=form, title="New Promotion")


@promo_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id: int):
    """Edit an existing promo."""
    session = get_session()
    promo = session.query(Promo).get(id)

    if not promo:
        flash("Promotion not found.", "danger")
        return redirect(url_for("promo.list"))

    form = PromoForm(obj=promo)

    # For edit, we show the current track
    form.track_id.choices = [(str(promo.track_id), promo.track.title)]

    if form.validate_on_submit():
        promo.track_art_definition = form.track_art_definition.data or None
        promo.canvas_definition = form.canvas_definition.data or None
        promo.pitch = form.pitch.data or None
        promo.summary = form.summary.data or None
        session.commit()

        flash("Promotion updated successfully.", "success")
        return redirect(url_for("promo.edit", id=id))

    # Get links
    links = session.query(PromoLink).filter_by(promo_id=id).all()

    return render_template(
        "promo/form.html",
        form=form,
        title="Edit Promotion",
        promo=promo,
        links=links,
    )


@promo_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id: int):
    """Delete a promo."""
    session = get_session()
    promo = session.query(Promo).get(id)

    if not promo:
        flash("Promotion not found.", "danger")
        return redirect(url_for("promo.list"))

    # Delete associated links
    session.query(PromoLink).filter_by(promo_id=id).delete()

    session.delete(promo)
    session.commit()

    flash("Promotion deleted successfully.", "success")
    return redirect(url_for("promo.list"))


@promo_bp.route("/<int:id>/links/add", methods=["POST"])
def add_link(id: int):
    """Add a link to a promo."""
    session = get_session()
    promo = session.query(Promo).get(id)

    if not promo:
        flash("Promotion not found.", "danger")
        return redirect(url_for("promo.list"))

    url = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()

    if url:
        link = PromoLink(
            promo_id=id,
            url=url,
            title=title or None,
        )
        session.add(link)
        session.commit()
        flash("Link added.", "success")
    else:
        flash("URL is required.", "danger")

    return redirect(url_for("promo.edit", id=id))


@promo_bp.route("/<int:id>/links/<int:link_id>/delete", methods=["POST"])
def delete_link(id: int, link_id: int):
    """Delete a link from a promo."""
    session = get_session()
    link = session.query(PromoLink).filter_by(id=link_id, promo_id=id).first()

    if link:
        session.delete(link)
        session.commit()
        flash("Link deleted.", "success")
    else:
        flash("Link not found.", "danger")

    return redirect(url_for("promo.edit", id=id))
