"""Definitions views for Sonnerrise web interface."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from sonnerrise_definitions import Definition, DefinitionLink, DefinitionRepository
from sonnerrise_personas import Persona
from sonnerrise_tracks import Track
from sonnerrise_web.app import get_session
from sonnerrise_web.forms import DefinitionForm, LinkForm

definitions_bp = Blueprint("definitions", __name__)


@definitions_bp.route("/")
def list():
    """List all definitions with pagination and filtering."""
    session = get_session()

    # Get filter parameters
    search = request.args.get("search", "").strip()
    service = request.args.get("service", "")
    model = request.args.get("model", "")
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Build query
    query = session.query(Definition)

    if search:
        query = query.filter(
            (Definition.title.ilike(f"%{search}%"))
            | (Definition.style_of_music.ilike(f"%{search}%"))
        )

    if service:
        query = query.filter(Definition.service == service)

    if model:
        query = query.filter(Definition.model == model)

    # Get total count
    total = query.count()

    # Paginate
    definitions = (
        query.order_by(Definition.title)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "definitions/list.html",
        definitions=definitions,
        search=search,
        service=service,
        model=model,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@definitions_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new definition."""
    session = get_session()
    form = DefinitionForm()

    # Populate persona choices
    personas = session.query(Persona).order_by(Persona.name).all()
    form.persona_id.choices = [("", "None")] + [
        (str(p.id), p.name) for p in personas
    ]

    # Populate track choices for cover_of
    tracks = session.query(Track).order_by(Track.title).all()
    form.cover_of_track_id.choices = [("", "None")] + [
        (str(t.id), t.title) for t in tracks
    ]

    if form.validate_on_submit():
        definition = Definition(
            title=form.title.data,
            annotation=form.annotation.data or None,
            service=form.service.data,
            model=form.model.data,
            style_of_music=form.style_of_music.data or None,
            older_models_style=form.older_models_style.data,
            lyrics=form.lyrics.data or None,
            persona_type=form.persona_type.data if form.persona_type.data != "none" else None,
            persona_id=form.persona_id.data,
            vocals=form.vocals.data,
            audio_influence=form.audio_influence.data,
            style_influence=form.style_influence.data,
            weirdness=form.weirdness.data,
            cover_of_track_id=form.cover_of_track_id.data,
            comments=form.comments.data or None,
        )
        session.add(definition)
        session.commit()

        flash("Definition created successfully.", "success")
        return redirect(url_for("definitions.list"))

    return render_template("definitions/form.html", form=form, title="New Definition")


@definitions_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id: int):
    """Edit an existing definition."""
    session = get_session()
    definition = session.query(Definition).get(id)

    if not definition:
        flash("Definition not found.", "danger")
        return redirect(url_for("definitions.list"))

    form = DefinitionForm(obj=definition)

    # Populate persona choices
    personas = session.query(Persona).order_by(Persona.name).all()
    form.persona_id.choices = [("", "None")] + [
        (str(p.id), p.name) for p in personas
    ]

    # Populate track choices for cover_of
    tracks = session.query(Track).order_by(Track.title).all()
    form.cover_of_track_id.choices = [("", "None")] + [
        (str(t.id), t.title) for t in tracks
    ]

    # Set persona_type properly for display
    if request.method == "GET" and definition.persona_type:
        form.persona_type.data = definition.persona_type

    if form.validate_on_submit():
        definition.title = form.title.data
        definition.annotation = form.annotation.data or None
        definition.service = form.service.data
        definition.model = form.model.data
        definition.style_of_music = form.style_of_music.data or None
        definition.older_models_style = form.older_models_style.data
        definition.lyrics = form.lyrics.data or None
        definition.persona_type = form.persona_type.data if form.persona_type.data != "none" else None
        definition.persona_id = form.persona_id.data
        definition.vocals = form.vocals.data
        definition.audio_influence = form.audio_influence.data
        definition.style_influence = form.style_influence.data
        definition.weirdness = form.weirdness.data
        definition.cover_of_track_id = form.cover_of_track_id.data
        definition.comments = form.comments.data or None
        session.commit()

        flash("Definition updated successfully.", "success")
        return redirect(url_for("definitions.list"))

    # Get links for this definition
    links = session.query(DefinitionLink).filter_by(definition_id=id).all()

    return render_template(
        "definitions/form.html",
        form=form,
        title="Edit Definition",
        definition=definition,
        links=links,
    )


@definitions_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id: int):
    """Delete a definition."""
    session = get_session()
    definition = session.query(Definition).get(id)

    if not definition:
        flash("Definition not found.", "danger")
        return redirect(url_for("definitions.list"))

    # Delete associated links
    session.query(DefinitionLink).filter_by(definition_id=id).delete()

    session.delete(definition)
    session.commit()

    flash("Definition deleted successfully.", "success")
    return redirect(url_for("definitions.list"))


@definitions_bp.route("/<int:id>/links/add", methods=["POST"])
def add_link(id: int):
    """Add a link to a definition."""
    session = get_session()
    definition = session.query(Definition).get(id)

    if not definition:
        flash("Definition not found.", "danger")
        return redirect(url_for("definitions.list"))

    url = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()

    if url:
        link = DefinitionLink(
            definition_id=id,
            url=url,
            title=title or None,
        )
        session.add(link)
        session.commit()
        flash("Link added.", "success")
    else:
        flash("URL is required.", "danger")

    return redirect(url_for("definitions.edit", id=id))


@definitions_bp.route("/<int:id>/links/<int:link_id>/delete", methods=["POST"])
def delete_link(id: int, link_id: int):
    """Delete a link from a definition."""
    session = get_session()
    link = session.query(DefinitionLink).filter_by(id=link_id, definition_id=id).first()

    if link:
        session.delete(link)
        session.commit()
        flash("Link deleted.", "success")
    else:
        flash("Link not found.", "danger")

    return redirect(url_for("definitions.edit", id=id))
