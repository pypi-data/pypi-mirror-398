"""Flask application factory for Sonnerrise web interface."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flask import Flask, g
from flask_wtf.csrf import CSRFProtect

from sonnerrise_core import get_database, load_config

csrf = CSRFProtect()

if TYPE_CHECKING:
    from sonnerrise_core import SonnerriseConfig
    from sonnerrise_core.database import DatabasePlugin


def create_app(config: SonnerriseConfig | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional Sonnerrise configuration. If not provided,
                configuration is loaded from default locations.

    Returns:
        Configured Flask application.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Load Sonnerrise config
    if config is None:
        config = load_config()

    # Store config in app
    app.sonnerrise_config = config

    # Flask configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["WTF_CSRF_ENABLED"] = True

    # Initialize CSRF protection
    csrf.init_app(app)

    # Initialize database
    app.database = get_database(config)

    # Register database session management
    @app.before_request
    def before_request():
        """Open database session before each request."""
        g.db_session = app.database.get_session()

    @app.teardown_request
    def teardown_request(exception=None):
        """Close database session after each request."""
        session = g.pop("db_session", None)
        if session is not None:
            if exception:
                session.rollback()
            session.close()

    # Register blueprints
    from sonnerrise_web.views.calendar import calendar_bp
    from sonnerrise_web.views.definitions import definitions_bp
    from sonnerrise_web.views.home import home_bp
    from sonnerrise_web.views.personas import personas_bp
    from sonnerrise_web.views.promo import promo_bp
    from sonnerrise_web.views.tools import tools_bp
    from sonnerrise_web.views.tracks import tracks_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(personas_bp, url_prefix="/personas")
    app.register_blueprint(definitions_bp, url_prefix="/definitions")
    app.register_blueprint(tracks_bp, url_prefix="/tracks")
    app.register_blueprint(promo_bp, url_prefix="/promo")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(tools_bp, url_prefix="/tools")

    # Context processors
    @app.context_processor
    def inject_navigation():
        """Inject navigation items into all templates."""
        return {
            "nav_items": [
                {"name": "Home", "url": "/", "icon": "home"},
                {"name": "Personas", "url": "/personas", "icon": "users"},
                {"name": "Definitions", "url": "/definitions", "icon": "file-text"},
                {"name": "Tracks", "url": "/tracks", "icon": "music"},
                {"name": "Promotion", "url": "/promo", "icon": "megaphone"},
                {"name": "Calendar", "url": "/calendar", "icon": "calendar"},
                {"name": "Tools", "url": "/tools", "icon": "wrench"},
            ]
        }

    return app


def get_session():
    """Get the current database session.

    Returns:
        Current SQLAlchemy session from Flask g object.
    """
    return g.db_session


def get_db():
    """Get the database plugin.

    Returns:
        The DatabasePlugin instance from the current app.
    """
    from flask import current_app
    return current_app.database
