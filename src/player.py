"""
player.py — Simulates music playback in the UI.

Since we don't have actual audio files for 30k Spotify tracks,
this module duplicates the playback experience.  It shows a "now playing"
card with track info and a progress bar that ticks forward.
"""

import time


class MusicPlayer:
    """
    Simple stateful player that tracks which song is currently playing.
    The Streamlit app reads from this to render the now-playing card.
    """

    def __init__(self):
        self.current_song = None
        self.is_playing = False
        self.elapsed_ms = 0

    def play(self, song_info):
        """
        Start 'playing' a song.

        Parameters
        ----------
        song_info : dict
            Must have at least 'track_name', 'track_artist',
            'track_album_name', 'duration_ms'.
        """
        self.current_song = song_info
        self.is_playing = True
        self.elapsed_ms = 0
        print(f"[player] Now playing: {song_info['track_name']} by {song_info['track_artist']}")

    def pause(self):
        self.is_playing = False

    def resume(self):
        if self.current_song:
            self.is_playing = True

    def stop(self):
        self.current_song = None
        self.is_playing = False
        self.elapsed_ms = 0

    def get_progress(self):
        """Return progress as a float between 0.0 and 1.0."""
        if not self.current_song:
            return 0.0
        total = self.current_song.get("duration_ms", 1)
        if total <= 0:
            return 0.0
        return min(self.elapsed_ms / total, 1.0)

    def format_duration(self, ms):
        """Turn milliseconds into a mm:ss string."""
        total_seconds = int(ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def now_playing_text(self):
        """Return a human-readable 'now playing' string."""
        if not self.current_song:
            return "Nothing playing"

        song = self.current_song
        duration_str = self.format_duration(song.get("duration_ms", 0))
        elapsed_str = self.format_duration(self.elapsed_ms)

        return (
            f"🎵 {song['track_name']}\n"
            f"   {song['track_artist']} — {song.get('track_album_name', 'Unknown Album')}\n"
            f"   [{elapsed_str} / {duration_str}]"
        )
