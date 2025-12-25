"""WTForms forms for Sonnerrise web interface."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FileField,
    IntegerField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PersonaForm(FlaskForm):
    """Form for creating/editing personas."""

    name = StringField(
        "Name",
        validators=[DataRequired(), Length(max=48)],
        render_kw={"placeholder": "Persona name"},
    )
    style_of_music = TextAreaField(
        "Style of Music",
        validators=[Length(max=1000)],
        render_kw={"placeholder": "Style of music (optional)", "rows": 3},
    )
    parental_track_id = SelectField(
        "Parental Track",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )
    comments = TextAreaField(
        "Comments",
        validators=[Length(max=32768)],
        render_kw={"rows": 4},
    )


class DefinitionForm(FlaskForm):
    """Form for creating/editing definitions."""

    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=120)],
        render_kw={"placeholder": "Definition title"},
    )
    annotation = TextAreaField(
        "Annotation",
        validators=[Length(max=200)],
        render_kw={"placeholder": "Brief annotation (optional)", "rows": 2},
    )
    service = SelectField(
        "Service",
        choices=[("suno", "Suno")],
        default="suno",
    )
    model = SelectField(
        "Model Version",
        choices=[
            ("v3.5", "v3.5"),
            ("v4.0", "v4.0"),
            ("v4.5+", "v4.5+"),
            ("v5.0", "v5.0"),
        ],
        default="v4.0",
    )
    style_of_music = TextAreaField(
        "Style of Music",
        validators=[Length(max=1000)],
        render_kw={"placeholder": "Style of music", "rows": 3},
    )
    older_models_style = BooleanField(
        "Older Models (limit style to 200 chars)",
        default=False,
    )
    lyrics = TextAreaField(
        "Lyrics",
        validators=[Length(max=3000)],
        render_kw={"placeholder": "Lyrics (optional)", "rows": 6},
    )
    persona_type = SelectField(
        "Persona Usage",
        choices=[
            ("none", "None"),
            ("voice", "Voice"),
            ("style", "Style"),
        ],
        default="none",
    )
    persona_id = SelectField(
        "Persona",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )
    vocals = SelectField(
        "Vocals",
        choices=[
            ("any", "Any"),
            ("female", "Female"),
            ("male", "Male"),
        ],
        default="any",
    )
    audio_influence = IntegerField(
        "Audio Influence",
        validators=[NumberRange(min=0, max=100)],
        default=25,
    )
    style_influence = IntegerField(
        "Style Influence",
        validators=[NumberRange(min=0, max=100)],
        default=50,
    )
    weirdness = IntegerField(
        "Weirdness",
        validators=[NumberRange(min=0, max=100)],
        default=50,
    )
    cover_of_track_id = SelectField(
        "Cover Of",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )
    comments = TextAreaField(
        "Comments",
        validators=[Length(max=32768)],
        render_kw={"rows": 4},
    )


class TrackForm(FlaskForm):
    """Form for creating/editing tracks."""

    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=120)],
        render_kw={"placeholder": "Track title"},
    )
    album = StringField(
        "Album / Playlist",
        validators=[Length(max=120)],
        render_kw={"placeholder": "Album or playlist name (optional)"},
    )
    definition_id = SelectField(
        "Definition",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )
    cover_art_url = StringField(
        "Cover Art URL",
        validators=[Length(max=500)],
        render_kw={"placeholder": "https://..."},
    )
    lyrics = TextAreaField(
        "Lyrics",
        validators=[Length(max=32768)],
        render_kw={"rows": 6},
    )
    comments = TextAreaField(
        "Comments",
        validators=[Length(max=32768)],
        render_kw={"rows": 4},
    )


class TrackEventForm(FlaskForm):
    """Form for creating/editing track events."""

    event_date = StringField(
        "Date/Time",
        validators=[DataRequired()],
        render_kw={"type": "datetime-local"},
    )
    description = StringField(
        "Description",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "e.g., Publish to Distrokid"},
    )
    is_enabled = BooleanField("Enabled", default=True)


class PromoForm(FlaskForm):
    """Form for creating/editing promotions."""

    track_id = SelectField(
        "Track",
        coerce=int,
        validators=[DataRequired()],
    )
    track_art_definition = TextAreaField(
        "Track Art Definition",
        validators=[Length(max=32768)],
        render_kw={
            "placeholder": "AI art generation prompt for still images",
            "rows": 4,
        },
    )
    canvas_definition = TextAreaField(
        "Canvas Definition",
        validators=[Length(max=32768)],
        render_kw={
            "placeholder": "AI generation prompt for short videos",
            "rows": 4,
        },
    )
    pitch = TextAreaField(
        "Pitch",
        validators=[Length(max=32768)],
        render_kw={
            "placeholder": "Pitch/blurb/promo text snippets",
            "rows": 4,
        },
    )
    summary = TextAreaField(
        "Summary",
        validators=[Length(max=32768)],
        render_kw={"rows": 4},
    )


class LinkForm(FlaskForm):
    """Form for adding links."""

    url = StringField(
        "URL",
        validators=[DataRequired(), Length(max=500)],
        render_kw={"placeholder": "https://..."},
    )
    title = StringField(
        "Title",
        validators=[Length(max=120)],
        render_kw={"placeholder": "Link title (optional)"},
    )


class ImportForm(FlaskForm):
    """Form for importing database."""

    file = FileField("Backup File", validators=[DataRequired()])
    skip_existing = BooleanField("Skip existing records", default=False)
    clear_existing = BooleanField("Clear existing data first", default=False)
