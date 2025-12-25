"""Personas views for Sonnerrise web interface."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from sonnerrise_personas import Persona, PersonaRepository
from sonnerrise_tracks import Track
from sonnerrise_web.app import get_session
from sonnerrise_web.forms import PersonaForm

personas_bp = Blueprint("personas", __name__)


@personas_bp.route("/")
def list():
    """List all personas with pagination and filtering."""
    session = get_session()
    repo = PersonaRepository(session)

    # Get filter parameters
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Build query
    query = session.query(Persona)

    if search:
        query = query.filter(Persona.name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Paginate
    personas = (
        query.order_by(Persona.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "personas/list.html",
        personas=personas,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@personas_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new persona."""
    session = get_session()
    form = PersonaForm()

    # Populate track choices
    tracks = session.query(Track).order_by(Track.title).all()
    form.parental_track_id.choices = [("", "None")] + [
        (str(t.id), t.title) for t in tracks
    ]

    if form.validate_on_submit():
        persona = Persona(
            name=form.name.data,
            style_of_music=form.style_of_music.data or None,
            parental_track_id=form.parental_track_id.data,
            comments=form.comments.data or None,
        )
        session.add(persona)
        session.commit()

        flash("Persona created successfully.", "success")
        return redirect(url_for("personas.list"))

    return render_template("personas/form.html", form=form, title="New Persona")


@personas_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id: int):
    """Edit an existing persona."""
    session = get_session()
    persona = session.query(Persona).get(id)

    if not persona:
        flash("Persona not found.", "danger")
        return redirect(url_for("personas.list"))

    form = PersonaForm(obj=persona)

    # Populate track choices
    tracks = session.query(Track).order_by(Track.title).all()
    form.parental_track_id.choices = [("", "None")] + [
        (str(t.id), t.title) for t in tracks
    ]

    if form.validate_on_submit():
        persona.name = form.name.data
        persona.style_of_music = form.style_of_music.data or None
        persona.parental_track_id = form.parental_track_id.data
        persona.comments = form.comments.data or None
        session.commit()

        flash("Persona updated successfully.", "success")
        return redirect(url_for("personas.list"))

    return render_template(
        "personas/form.html",
        form=form,
        title="Edit Persona",
        persona=persona,
    )


@personas_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id: int):
    """Delete a persona."""
    session = get_session()
    persona = session.query(Persona).get(id)

    if not persona:
        flash("Persona not found.", "danger")
        return redirect(url_for("personas.list"))

    session.delete(persona)
    session.commit()

    flash("Persona deleted successfully.", "success")
    return redirect(url_for("personas.list"))
