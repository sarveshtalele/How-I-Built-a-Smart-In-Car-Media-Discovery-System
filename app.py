"""
app.py — Streamlit frontend for the Smart In-Car Media Discovery System.

Run with:
    streamlit run app.py

The UI mimics a car infotainment screen: dark theme, big touch-friendly
buttons, and a prominent voice search button.  Users can either type a
query or upload a voice recording, and the system returns matching songs
from the local Qdrant Edge shard.
"""

import sys
import os
import time

import streamlit as st

# make sure our src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from search import search_songs, search_by_mood
from voice import transcribe_uploaded_audio, transcribe_audio_file
from player import MusicPlayer
from config import DEFAULT_TOP_K


# ── Page setup ─────────────────────────────────────────────────
st.set_page_config(
    page_title="CarTune — In-Car Media Discovery",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS for a car-dashboard feel ────────────────────────
st.markdown("""
<style>
    /* dark automotive theme */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* big header */
    .car-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(90deg, #0f3460, #533483);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(83, 52, 131, 0.3);
    }
    .car-header h1 {
        color: #e94560;
        font-size: 2.5rem;
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
    }
    .car-header p {
        color: #a8a8b3;
        font-size: 1.1rem;
        margin: 0.3rem 0 0 0;
    }

    /* song cards */
    .song-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(233, 69, 96, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
    }
    .song-card:hover {
        background: rgba(233, 69, 96, 0.1);
        border-color: #e94560;
        transform: translateX(5px);
    }
    .song-title {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 600;
        margin: 0;
    }
    .song-artist {
        color: #e94560;
        font-size: 0.95rem;
        margin: 0.2rem 0;
    }
    .song-meta {
        color: #6c6c80;
        font-size: 0.8rem;
    }

    /* now-playing bar */
    .now-playing {
        background: linear-gradient(90deg, #1a1a2e, #0f3460);
        border: 2px solid #e94560;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin-top: 1rem;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 0 10px rgba(233, 69, 96, 0.3); }
        to   { box-shadow: 0 0 25px rgba(233, 69, 96, 0.6); }
    }
    .now-playing h3 {
        color: #e94560;
        margin: 0 0 0.5rem 0;
    }
    .now-playing .np-track {
        color: #ffffff;
        font-size: 1.3rem;
        font-weight: bold;
    }
    .now-playing .np-artist {
        color: #a8a8b3;
        font-size: 1rem;
    }

    /* mood buttons */
    .stButton > button {
        border-radius: 25px;
        border: 1px solid rgba(233, 69, 96, 0.5);
        background: rgba(233, 69, 96, 0.1);
        color: #e94560;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #e94560;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────
if "player" not in st.session_state:
    st.session_state.player = MusicPlayer()
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="car-header">
    <h1>🚗 CarTune</h1>
    <p>Smart In-Car Media Discovery — Powered by Qdrant Edge + Whisper</p>
</div>
""", unsafe_allow_html=True)


# ── Layout: two columns — search on left, now-playing on right ─
col_search, col_player = st.columns([3, 2])

with col_search:
    st.markdown("### 🔍 Find Your Song")

    # ── Tab layout: Text search vs Voice search ────────────────
    tab_text, tab_voice, tab_mood = st.tabs(["⌨️ Type", "🎙️ Voice", "🎭 Mood"])

    with tab_text:
        text_query = st.text_input(
            "What do you want to hear?",
            placeholder="e.g. upbeat pop song by Ed Sheeran",
            label_visibility="collapsed",
        )
        top_k = st.slider("Number of results", min_value=1, max_value=20, value=DEFAULT_TOP_K)

        if st.button("Search", key="text_search", use_container_width=True):
            if text_query.strip():
                with st.spinner("Searching your library ..."):
                    st.session_state.search_results = search_songs(text_query.strip(), top_k=top_k)
                    st.session_state.last_query = text_query.strip()

    with tab_voice:
        st.markdown("Record your voice request:")

        audio_value = st.audio_input("Record a voice message", label_visibility="collapsed")

        if audio_value is not None:
            if st.button("🎙️ Transcribe & Search", key="voice_search", use_container_width=True):
                with st.spinner("Transcribing with Whisper ..."):
                    audio_bytes = audio_value.read()
                    transcribed_text = transcribe_uploaded_audio(audio_bytes, suffix=".wav")

                st.success(f"**You said:** {transcribed_text}")

                with st.spinner("Searching ..."):
                    st.session_state.search_results = search_songs(transcribed_text, top_k=DEFAULT_TOP_K)
                    st.session_state.last_query = transcribed_text

    with tab_mood:
        st.markdown("Pick a mood and we'll find songs that match:")

        mood_cols = st.columns(3)
        moods = [
            ("😊 Happy", "happy"),
            ("😢 Sad", "sad"),
            ("⚡ Energetic", "energetic"),
            ("😌 Chill", "chill"),
            ("❤️ Romantic", "romantic"),
            ("🎉 Party", "party"),
        ]

        for i, (label, mood_key) in enumerate(moods):
            with mood_cols[i % 3]:
                if st.button(label, key=f"mood_{mood_key}", use_container_width=True):
                    with st.spinner(f"Finding {mood_key} songs ..."):
                        st.session_state.search_results = search_by_mood(mood_key, top_k=DEFAULT_TOP_K)
                        st.session_state.last_query = f"Mood: {mood_key}"


# ── Display search results ─────────────────────────────────────
with col_search:
    if st.session_state.search_results:
        st.markdown(f"---")
        st.markdown(f"**Results for:** *{st.session_state.last_query}*")

        for i, song in enumerate(st.session_state.search_results):
            duration_min = song.get("duration_ms", 0) / 60000
            popularity = song.get("track_popularity", 0)

            col_info, col_play = st.columns([5, 1])

            with col_info:
                st.markdown(f"""
                <div class="song-card">
                    <p class="song-title">{i+1}. {song['track_name']}</p>
                    <p class="song-artist">{song['track_artist']}</p>
                    <p class="song-meta">
                        {song.get('track_album_name', '')} •
                        {song.get('playlist_genre', '')} / {song.get('playlist_subgenre', '')} •
                        {duration_min:.1f} min •
                        Popularity: {popularity}/100
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_play:
                if st.button("▶️", key=f"play_{i}", help=f"Play {song['track_name']}"):
                    st.session_state.player.play(song)
                    st.rerun()


# ── Now Playing panel ──────────────────────────────────────────
with col_player:
    st.markdown("### 🎵 Now Playing")

    player = st.session_state.player

    if player.current_song:
        song = player.current_song
        duration_str = player.format_duration(song.get("duration_ms", 0))

        st.markdown(f"""
        <div class="now-playing">
            <h3>♫ NOW PLAYING</h3>
            <p class="np-track">{song['track_name']}</p>
            <p class="np-artist">{song['track_artist']}</p>
            <p style="color: #6c6c80; font-size: 0.85rem;">
                {song.get('track_album_name', 'Unknown Album')} • {duration_str}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # simulated progress bar
        st.progress(player.get_progress())

        # playback controls
        ctrl_cols = st.columns(3)
        with ctrl_cols[0]:
            if st.button("⏸️ Pause", use_container_width=True):
                player.pause()
        with ctrl_cols[1]:
            if st.button("▶️ Resume", use_container_width=True):
                player.resume()
        with ctrl_cols[2]:
            if st.button("⏹️ Stop", use_container_width=True):
                player.stop()
                st.rerun()

        # song details in an expander
        with st.expander("Song Details"):
            detail_cols = st.columns(2)
            with detail_cols[0]:
                st.metric("Energy", f"{song.get('energy', 0):.2f}")
                st.metric("Danceability", f"{song.get('danceability', 0):.2f}")
                st.metric("Tempo", f"{song.get('tempo', 0):.0f} BPM")
            with detail_cols[1]:
                st.metric("Valence (Happiness)", f"{song.get('valence', 0):.2f}")
                st.metric("Popularity", f"{song.get('track_popularity', 0)}/100")
                st.metric("Genre", song.get("playlist_genre", "N/A"))
    else:
        st.markdown("""
        <div class="now-playing" style="opacity: 0.5;">
            <h3>♫ NO TRACK SELECTED</h3>
            <p style="color: #6c6c80;">Search for a song and hit play</p>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#6c6c80; font-size:0.8rem;'>"
    "CarTune — Built with Qdrant Edge, Whisper & FastEmbed | "
    "All search runs locally, no cloud required"
    "</p>",
    unsafe_allow_html=True,
)
