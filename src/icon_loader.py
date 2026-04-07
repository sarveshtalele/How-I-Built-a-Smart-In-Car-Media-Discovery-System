"""
icon_loader.py — Dynamic PNG icon loader for CarTune.

Loads icons from the project-level `icons/` folder at runtime.
No hardcoded SVG paths — every icon is a real PNG file on disk,
base64-encoded and served as an inline <img> tag.

Available icons (from the icons/ folder):
    music-note.png          — Music note in circle (branding / headers)
    play-buttton.png        — Solid play triangle (play controls)
    play.png                — Skip-next icon (forward controls)
    video-pause-button.png  — Pause button in circle (pause controls)

Usage:
    from icon_loader import load_icon
    st.markdown(f"{load_icon('music-note.png', 32)} CarTune", unsafe_allow_html=True)
"""

from __future__ import annotations

import base64
from pathlib import Path
from functools import lru_cache

# Root directory for all PNG icons
_ICONS_DIR = Path(__file__).resolve().parent.parent / "icons"


@lru_cache(maxsize=32)
def _read_icon_b64(filename: str) -> str | None:
    """Read a PNG file from the icons folder and return its base64 string (cached)."""
    icon_path = _ICONS_DIR / filename
    if not icon_path.exists():
        return None
    with open(icon_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_icon(
    filename: str,
    size: int = 24,
    invert: bool = True,
    css: str = "",
) -> str:
    """
    Return an HTML <img> tag with the base64-encoded PNG from icons/.

    Parameters
    ----------
    filename : str
        PNG filename inside the icons/ folder (e.g. "music-note.png").
    size : int
        Width and height in pixels.
    invert : bool
        If True, applies CSS `filter: invert(1)` to turn black icons white
        (needed for dark-theme display).
    css : str
        Extra inline CSS to append to the style attribute.

    Returns
    -------
    str
        An <img> element ready for Streamlit unsafe_allow_html.
        Returns an empty string if the icon file is not found.
    """
    b64 = _read_icon_b64(filename)
    if b64 is None:
        return ""

    invert_css = "filter: invert(1);" if invert else ""
    extra = f" {css}" if css else ""

    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'width="{size}" height="{size}" '
        f'style="vertical-align: middle; object-fit: contain; {invert_css}{extra}" />'
    )


def load_icon_b64_src(filename: str) -> str:
    """
    Return just the base64 data-URI string for an icon.
    Useful for embedding in custom HTML components (e.g. the audio player).
    """
    b64 = _read_icon_b64(filename)
    if b64 is None:
        return ""
    return f"data:image/png;base64,{b64}"


def list_icons() -> list[str]:
    """List all PNG files available in the icons/ folder."""
    if not _ICONS_DIR.exists():
        return []
    return sorted(f.name for f in _ICONS_DIR.glob("*.png"))
