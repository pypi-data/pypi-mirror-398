"""Tools views for Sonnerrise web interface."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from sonnerrise_tools import ExportService, ImportService
from sonnerrise_tools.schemas import ExportOptions, ImportOptions
from sonnerrise_web.app import get_session
from sonnerrise_web.forms import ImportForm

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/")
def index():
    """Show tools page."""
    session = get_session()

    # Get database stats
    from sonnerrise_definitions import Definition, DefinitionLink
    from sonnerrise_personas import Persona
    from sonnerrise_promo import Promo, PromoLink
    from sonnerrise_tracks import Track, TrackEvent, TrackLink

    stats = {
        "personas": session.query(Persona).count(),
        "definitions": session.query(Definition).count(),
        "definition_links": session.query(DefinitionLink).count(),
        "tracks": session.query(Track).count(),
        "track_links": session.query(TrackLink).count(),
        "track_events": session.query(TrackEvent).count(),
        "promos": session.query(Promo).count(),
        "promo_links": session.query(PromoLink).count(),
    }
    stats["total"] = sum(stats.values())

    form = ImportForm()

    return render_template("tools/index.html", stats=stats, form=form)


@tools_bp.route("/export", methods=["POST"])
def export():
    """Export database to downloadable file."""
    session = get_session()

    # Get export options
    format_type = request.form.get("format", "json")
    include_personas = request.form.get("include_personas") == "on"
    include_definitions = request.form.get("include_definitions") == "on"
    include_tracks = request.form.get("include_tracks") == "on"
    include_promos = request.form.get("include_promos") == "on"

    options = ExportOptions(
        include_personas=include_personas,
        include_definitions=include_definitions,
        include_tracks=include_tracks,
        include_promos=include_promos,
        pretty_print=True,
    )

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f".{format_type}") as f:
        temp_path = f.name

    exporter = ExportService(session)
    backup = exporter.export_all(temp_path, format=format_type, options=options)

    # Read file content
    with open(temp_path, "r") as f:
        content = f.read()

    # Clean up temp file
    Path(temp_path).unlink()

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sonnerrise_backup_{timestamp}.{format_type}"

    # Set content type
    if format_type == "yaml":
        content_type = "application/x-yaml"
    else:
        content_type = "application/json"

    return Response(
        content,
        mimetype=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@tools_bp.route("/import", methods=["POST"])
def import_data():
    """Import database from uploaded file."""
    session = get_session()
    form = ImportForm()

    if not form.validate_on_submit():
        flash("Please select a file to import.", "danger")
        return redirect(url_for("tools.index"))

    file = form.file.data

    if not file:
        flash("No file selected.", "danger")
        return redirect(url_for("tools.index"))

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        file.save(f)
        temp_path = f.name

    try:
        # Determine file format from extension
        filename = file.filename or ""
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            # YAML file, no change needed
            pass
        else:
            # Assume JSON
            pass

        importer = ImportService(session)

        options = ImportOptions(
            skip_existing=form.skip_existing.data,
            clear_existing=form.clear_existing.data,
            create_tables=True,
        )

        result = importer.import_all(temp_path, options=options)

        if result.success:
            flash(
                f"Successfully imported {result.imported.total} records. "
                f"Skipped {result.skipped.total} existing records.",
                "success",
            )
            if result.warnings:
                for warning in result.warnings:
                    flash(warning, "warning")
        else:
            flash("Import failed:", "danger")
            for error in result.errors:
                flash(error, "danger")

    except Exception as e:
        flash(f"Import error: {str(e)}", "danger")

    finally:
        # Clean up temp file
        Path(temp_path).unlink()

    return redirect(url_for("tools.index"))


@tools_bp.route("/validate", methods=["POST"])
def validate():
    """Validate an uploaded backup file."""
    file = request.files.get("file")

    if not file:
        flash("No file selected.", "danger")
        return redirect(url_for("tools.index"))

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        file.save(f)
        temp_path = f.name

    try:
        from sonnerrise_core import get_database, load_config

        config = load_config()
        db = get_database(config)

        with db.session() as session:
            importer = ImportService(session)

            # Get backup info
            info = importer.get_backup_info(temp_path)

            flash(
                f"Backup is valid. Version: {info.version}, "
                f"Records: {info.counts.total}, "
                f"Created: {info.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                "success" if info.is_compatible else "warning",
            )

            if not info.is_compatible:
                flash("Warning: Backup version may not be fully compatible.", "warning")

    except Exception as e:
        flash(f"Validation error: {str(e)}", "danger")

    finally:
        # Clean up temp file
        Path(temp_path).unlink()

    return redirect(url_for("tools.index"))
