"""
audio_player.py — Spotify-styled HTML5 audio player widget for CarTune.

Renders a self-contained HTML/CSS/JS audio player that uses PNG icons
loaded from the icons/ folder.  Designed to match the Spotify dark-theme
aesthetic: #121212 background, #1DB954 green accents, clean typography.

Usage:
    from audio_player import render_audio_player
    import streamlit.components.v1 as components

    html = render_audio_player(audio_bytes, title, artist, album, duration_str)
    components.html(html, height=200)
"""

from __future__ import annotations

import base64

from icon_loader import load_icon_b64_src


def render_audio_player(
    audio_bytes: bytes,
    title: str,
    artist: str,
    album: str = "",
    duration_str: str = "0:30",
) -> str:
    """
    Build a self-contained Spotify-styled HTML5 player block.

    Parameters
    ----------
    audio_bytes : bytes
        Raw MP3 file contents.
    title, artist, album : str
        Track metadata to render above the player.
    duration_str : str
        Human-readable total duration ("0:30").

    Returns
    -------
    str
        A full HTML document safe to drop into st.components.v1.html().
    """
    b64_audio = base64.b64encode(audio_bytes).decode("ascii")

    # Load PNG icons as base64 data URIs for the embedded HTML
    play_src  = load_icon_b64_src("play-buttton.png")
    pause_src = load_icon_b64_src("video-pause-button.png")
    next_src  = load_icon_b64_src("play.png")

    # Escape metadata for safe HTML rendering
    safe_title  = (title  or "Unknown Title").replace('"', "&quot;").replace("<", "&lt;")
    safe_artist = (artist or "Unknown Artist").replace('"', "&quot;").replace("<", "&lt;")
    safe_album  = (album  or "").replace('"', "&quot;").replace("<", "&lt;")

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        background: transparent;
    }}

    .sp-player {{
        background: #181818;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        color: #ffffff;
    }}

    /* ── Progress bar ── */
    .sp-progress {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }}
    .sp-progress .sp-time {{
        color: #b3b3b3;
        font-size: 0.7rem;
        font-variant-numeric: tabular-nums;
        min-width: 32px;
        text-align: center;
    }}
    .sp-seek {{
        flex: 1;
        -webkit-appearance: none;
        appearance: none;
        height: 4px;
        background: #4d4d4d;
        border-radius: 2px;
        outline: none;
        cursor: pointer;
        transition: height 0.15s;
    }}
    .sp-seek:hover {{
        height: 6px;
    }}
    .sp-seek::-webkit-slider-thumb {{
        -webkit-appearance: none;
        appearance: none;
        width: 12px;
        height: 12px;
        background: #ffffff;
        border-radius: 50%;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.15s;
    }}
    .sp-seek:hover::-webkit-slider-thumb {{
        opacity: 1;
    }}
    .sp-seek::-moz-range-thumb {{
        width: 12px;
        height: 12px;
        background: #ffffff;
        border-radius: 50%;
        border: none;
        cursor: pointer;
    }}
    .sp-seek::-webkit-slider-runnable-track {{
        background: linear-gradient(to right, #1DB954 0%, #1DB954 var(--progress, 0%), #4d4d4d var(--progress, 0%), #4d4d4d 100%);
        border-radius: 2px;
    }}

    /* ── Controls ── */
    .sp-controls {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.5rem;
    }}
    .sp-btn {{
        background: none;
        border: none;
        cursor: pointer;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.1s, opacity 0.15s;
        opacity: 0.8;
    }}
    .sp-btn:hover {{
        opacity: 1;
        transform: scale(1.08);
    }}
    .sp-btn img {{
        filter: invert(1);
    }}
    .sp-btn.sp-primary {{
        background: #1DB954;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        opacity: 1;
    }}
    .sp-btn.sp-primary:hover {{
        background: #1ed760;
        transform: scale(1.06);
    }}
    .sp-btn.sp-primary img {{
        filter: invert(0);  /* black icon on green bg */
    }}

    /* ── Volume ── */
    .sp-vol {{
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.4rem;
        margin-top: 0.8rem;
    }}
    .sp-vol label {{
        color: #727272;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .sp-vol input[type=range] {{
        width: 90px;
        -webkit-appearance: none;
        appearance: none;
        height: 3px;
        background: #4d4d4d;
        border-radius: 2px;
        outline: none;
    }}
    .sp-vol input[type=range]::-webkit-slider-thumb {{
        -webkit-appearance: none;
        width: 10px;
        height: 10px;
        background: #ffffff;
        border-radius: 50%;
        cursor: pointer;
    }}
</style>
</head>
<body>
    <div class="sp-player">
        <audio id="sp-audio" autoplay>
            <source src="data:audio/mpeg;base64,{b64_audio}" type="audio/mpeg" />
        </audio>

        <div class="sp-progress">
            <span class="sp-time" id="sp-cur">0:00</span>
            <input type="range" class="sp-seek" id="sp-seek" min="0" max="100" value="0" step="0.1" />
            <span class="sp-time" id="sp-tot">{duration_str}</span>
        </div>

        <div class="sp-controls">
            <button class="sp-btn" id="sp-prev" title="Rewind 5s">
                <img src="{next_src}" width="22" height="22" style="transform: scaleX(-1);" />
            </button>
            <button class="sp-btn sp-primary" id="sp-play" title="Play / Pause">
                <img src="{play_src}" width="24" height="24" id="sp-play-icon" />
            </button>
            <button class="sp-btn" id="sp-next" title="Forward 5s">
                <img src="{next_src}" width="22" height="22" />
            </button>
        </div>

        <div class="sp-vol">
            <label>Vol</label>
            <input type="range" id="sp-vol" min="0" max="1" value="0.85" step="0.05" />
        </div>
    </div>

    <script>
        (function() {{
            const audio = document.getElementById("sp-audio");
            const seek  = document.getElementById("sp-seek");
            const cur   = document.getElementById("sp-cur");
            const tot   = document.getElementById("sp-tot");
            const vol   = document.getElementById("sp-vol");
            const playBtn  = document.getElementById("sp-play");
            const playIcon = document.getElementById("sp-play-icon");

            const playSrc  = "{play_src}";
            const pauseSrc = "{pause_src}";

            const fmt = (t) => {{
                if (!isFinite(t) || t < 0) return "0:00";
                const m = Math.floor(t / 60);
                const s = Math.floor(t % 60);
                return m + ":" + (s < 10 ? "0" : "") + s;
            }};

            audio.volume = parseFloat(vol.value);

            audio.addEventListener("loadedmetadata", () => {{
                if (isFinite(audio.duration)) {{
                    tot.textContent = fmt(audio.duration);
                }}
            }});

            audio.addEventListener("timeupdate", () => {{
                if (audio.duration > 0) {{
                    const pct = (audio.currentTime / audio.duration) * 100;
                    seek.value = pct;
                    seek.style.setProperty('--progress', pct + '%');
                    cur.textContent = fmt(audio.currentTime);
                }}
            }});

            audio.addEventListener("ended", () => {{
                seek.value = 0;
                seek.style.setProperty('--progress', '0%');
                cur.textContent = "0:00";
                playIcon.src = playSrc;
            }});

            audio.addEventListener("play", () => {{
                playIcon.src = pauseSrc;
            }});
            audio.addEventListener("pause", () => {{
                playIcon.src = playSrc;
            }});

            seek.addEventListener("input", () => {{
                if (audio.duration > 0) {{
                    audio.currentTime = (seek.value / 100) * audio.duration;
                }}
            }});

            vol.addEventListener("input", () => {{
                audio.volume = parseFloat(vol.value);
            }});

            playBtn.addEventListener("click", () => {{
                if (audio.paused) {{
                    audio.play();
                }} else {{
                    audio.pause();
                }}
            }});

            document.getElementById("sp-prev").addEventListener("click", () => {{
                audio.currentTime = Math.max(0, audio.currentTime - 5);
            }});
            document.getElementById("sp-next").addEventListener("click", () => {{
                if (audio.duration > 0) {{
                    audio.currentTime = Math.min(audio.duration, audio.currentTime + 5);
                }}
            }});

            // Try autoplay
            const p = audio.play();
            if (p !== undefined) {{
                p.catch(() => {{}});
            }}
        }})();
    </script>
</body>
</html>
"""
