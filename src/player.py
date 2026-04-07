"""
player.py — Real audio playback state for the Streamlit UI.

Unlike the previous version, which simulated playback with a fake elapsed
counter, this player loads the actual MP3 bytes from disk so the Streamlit
front-end can hand them to st.audio() for real browser playback.
"""

from __future__ import annotations

from pathlib import Path

from config import PROJECT_ROOT


class MusicPlayer:
    """
    Holds the currently selected song plus its raw MP3 bytes.

    The bytes are loaded once on .play() and stored in session state by the
    front-end so Streamlit reruns don't reset the audio element in the browser.
    """

    def __init__(self) -> None:
        self.current_song:   dict | None  = None
        self.is_playing:     bool         = False
        self.audio_path:     str | None   = None
        self.audio_bytes:    bytes | None = None
        self.error_message:  str | None   = None

    # ── core actions ───────────────────────────────────────────

    def play(self, song_info: dict) -> bool:
        """
        Load the MP3 for the given song and mark it as playing.

        Returns True on success, False if the audio file is missing or
        cannot be read.
        """
        self.current_song  = song_info
        self.error_message = None

        rel_path = song_info.get("audio_path", "")
        if not rel_path:
            self.error_message = "No audio_path stored for this song."
            self.audio_bytes = None
            self.audio_path  = None
            self.is_playing  = False
            return False

        # support both relative ("fma_small/000/000002.mp3") and absolute paths
        candidate = Path(rel_path)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate

        if not candidate.exists():
            self.error_message = f"Audio file not found: {candidate}"
            self.audio_bytes = None
            self.audio_path  = None
            self.is_playing  = False
            return False

        try:
            with candidate.open("rb") as f:
                self.audio_bytes = f.read()
        except Exception as e:
            self.error_message = f"Failed to read audio file: {e}"
            self.audio_bytes = None
            self.audio_path  = None
            self.is_playing  = False
            return False

        self.audio_path = str(candidate)
        self.is_playing = True
        print(f"[player] Now playing: {song_info.get('track_name')} "
              f"by {song_info.get('track_artist')} ({len(self.audio_bytes)} bytes)")
        return True

    def pause(self) -> None:
        self.is_playing = False

    def resume(self) -> None:
        if self.current_song is not None and self.audio_bytes is not None:
            self.is_playing = True

    def stop(self) -> None:
        self.current_song  = None
        self.audio_path    = None
        self.audio_bytes   = None
        self.is_playing    = False
        self.error_message = None

    # ── helpers ────────────────────────────────────────────────

    def get_audio_bytes(self) -> bytes | None:
        return self.audio_bytes

    def has_audio(self) -> bool:
        return self.audio_bytes is not None

    def format_duration(self, ms: int) -> str:
        """Turn milliseconds into a 'mm:ss' string."""
        total_seconds = int(ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def now_playing_text(self) -> str:
        """Plain-text status string for logging or fallback display."""
        if not self.current_song:
            return "Nothing playing"

        song = self.current_song
        duration_str = self.format_duration(song.get("duration_ms", 0))
        return (
            f"{song.get('track_name', 'Unknown')} - "
            f"{song.get('track_artist', 'Unknown')} "
            f"[{duration_str}]"
        )
