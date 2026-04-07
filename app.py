"""
app.py — Streamlit frontend for the Smart In-Car Media Discovery System.

Run with:
    streamlit run app.py

Professional Spotify-inspired music player UI with dark theme,
custom PNG icons loaded from the icons/ folder, and a real HTML5
audio player that streams MP3s from disk.

Search modes:
    1. Text   — type a natural-language query
    2. Voice  — record into the mic, Whisper transcribes, then search
    3. Mood   — one-tap mood buttons mapped to richer query phrases
"""

import sys
import os

import streamlit as st
import streamlit.components.v1 as components

# make sure our src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from search import search_songs, search_by_mood
from voice import transcribe_uploaded_audio
from player import MusicPlayer
from icon_loader import load_icon
from audio_player import render_audio_player
from config import DEFAULT_TOP_K


# ── Page setup ─────────────────────────────────────────────────
st.set_page_config(
    page_title="CarTune — Smart Music Discovery",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Spotify-inspired CSS ──────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global dark theme ── */
    .stApp {
        background: #121212;
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    p, li, span, label {
        font-family: 'Inter', sans-serif;
    }

    /* ── Header banner ── */
    .ct-header {
        padding: 2.5rem 2rem 2rem 2rem;
        background: linear-gradient(180deg, #1DB954 0%, #1a1a1a 100%);
        border-radius: 12px;
        margin-bottom: 1.8rem;
    }
    .ct-header h1 {
        color: #ffffff !important;
        font-size: 2.8rem;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .ct-header p {
        color: rgba(255,255,255,0.75);
        font-size: 1rem;
        margin: 0.4rem 0 0 0;
        font-weight: 400;
    }

    /* ── Section headings ── */
    .ct-section {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        letter-spacing: -0.3px;
    }

    /* ── Song cards ── */
    .ct-card {
        background: #181818;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: background-color 0.3s ease;
        border: none;
    }
    .ct-card:hover {
        background: #282828;
    }
    .ct-card .ct-title {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 0 0 0.2rem 0;
    }
    .ct-card .ct-artist {
        color: #1DB954;
        font-size: 0.9rem;
        font-weight: 500;
        margin: 0 0 0.2rem 0;
    }
    .ct-card .ct-meta {
        color: #a7a7a7;
        font-size: 0.8rem;
        margin: 0;
    }

    /* ── Now Playing panel ── */
    .ct-now-playing {
        background: linear-gradient(180deg, #282828 0%, #181818 100%);
        border-radius: 12px;
        padding: 1.8rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    .ct-now-playing .ct-np-label {
        color: #1DB954;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0 0 0.8rem 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .ct-now-playing .ct-np-track {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
    }
    .ct-now-playing .ct-np-artist {
        color: #b3b3b3;
        font-size: 1rem;
        margin: 0 0 0.3rem 0;
    }
    .ct-now-playing .ct-np-album {
        color: #727272;
        font-size: 0.85rem;
        margin: 0;
    }

    /* ── Empty state ── */
    .ct-empty {
        background: #181818;
        border-radius: 12px;
        padding: 3rem 1.5rem;
        text-align: center;
        opacity: 0.6;
    }
    .ct-empty p {
        color: #727272;
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
    }

    /* ── Buttons (Spotify pill style) ── */
    .stButton > button {
        border-radius: 500px !important;
        border: none !important;
        background: #1DB954 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.55rem 1.6rem !important;
        font-size: 0.9rem !important;
        transition: transform 0.1s ease, background-color 0.2s ease !important;
        letter-spacing: 0.3px !important;
    }
    .stButton > button:hover {
        background: #1ed760 !important;
        color: #000000 !important;
        transform: scale(1.04) !important;
    }
    .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* ── Text input (Spotify search bar) ── */
    div.stTextInput > div > div > input {
        background-color: #242424 !important;
        color: #ffffff !important;
        border: 1px solid transparent !important;
        border-radius: 500px !important;
        padding: 0.7rem 1.2rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
    }
    div.stTextInput > div > div > input:focus {
        border-color: #ffffff !important;
        box-shadow: none !important;
    }
    div.stTextInput > div > div > input::placeholder {
        color: #727272 !important;
    }

    /* ── Slider ── */
    .stSlider > div > div > div > div {
        background-color: #1DB954 !important;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #181818;
        border-radius: 500px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 500px;
        color: #b3b3b3;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        padding: 0.4rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        background: #282828 !important;
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        color: #b3b3b3 !important;
        font-weight: 600;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: #1DB954 !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #b3b3b3 !important;
    }

    /* ── Hide audio filename ── */
    .stAudio > div:first-child {
        display: none;
    }

    /* ── Divider ── */
    hr {
        border-color: #282828 !important;
    }

    /* ── Tab sub-label ── */
    .ct-tab-hint {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: #727272;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    /* ── Footer ── */
    .ct-footer {
        text-align: center;
        color: #535353;
        font-size: 0.75rem;
        padding: 1rem 0;
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
st.markdown(f"""
<div class="ct-header">
    <h1>{load_icon("music-note.png", 44)} CarTune</h1>
    <p>Smart In-Car Media Discovery — Powered by Qdrant Edge + Whisper</p>
</div>
""", unsafe_allow_html=True)


# ── Layout: two columns — search on left, now-playing on right ─
col_search, col_player = st.columns([3, 2])

with col_search:
    st.markdown(
        f'<div class="ct-section">{load_icon("music-note.png", 24)} Find Your Song</div>',
        unsafe_allow_html=True,
    )

    # ── Tab layout: Text search vs Voice search vs Mood ────────
    tab_text, tab_voice, tab_mood = st.tabs(["Type", "Voice", "Mood"])

    with tab_text:
        st.markdown(
            '<div class="ct-tab-hint">Type your request</div>',
            unsafe_allow_html=True,
        )
        text_query = st.text_input(
            "What do you want to hear?",
            placeholder="e.g. upbeat hip-hop, calm folk guitar, electronic dance ...",
            label_visibility="collapsed",
        )
        top_k = st.slider("Number of results", min_value=1, max_value=20, value=DEFAULT_TOP_K)

        if st.button("Search", key="text_search", use_container_width=True):
            if text_query.strip():
                with st.spinner("Searching your library ..."):
                    st.session_state.search_results = search_songs(
                        text_query.strip(), top_k=top_k
                    )
                    st.session_state.last_query = text_query.strip()

    with tab_voice:
        st.markdown(
            '<div class="ct-tab-hint">Record your voice request</div>',
            unsafe_allow_html=True,
        )

        audio_value = st.audio_input("Record a voice message", label_visibility="collapsed")

        if audio_value is not None:
            if st.button("Transcribe & Search", key="voice_search", use_container_width=True):
                with st.spinner("Transcribing with Whisper ..."):
                    audio_bytes = audio_value.read()
                    transcribed_text = transcribe_uploaded_audio(audio_bytes, suffix=".wav")

                st.success(f"**You said:** {transcribed_text}")

                with st.spinner("Searching ..."):
                    st.session_state.search_results = search_songs(
                        transcribed_text, top_k=DEFAULT_TOP_K
                    )
                    st.session_state.last_query = transcribed_text

    with tab_mood:
        st.markdown(
            '<div class="ct-tab-hint">Pick a mood and we\'ll find matching songs</div>',
            unsafe_allow_html=True,
        )

        mood_cols = st.columns(3)
        moods = [
            ("Happy",     "happy"),
            ("Sad",       "sad"),
            ("Energetic", "energetic"),
            ("Chill",     "chill"),
            ("Romantic",  "romantic"),
            ("Party",     "party"),
        ]

        for i, (label, mood_key) in enumerate(moods):
            with mood_cols[i % 3]:
                if st.button(label, key=f"mood_{mood_key}", use_container_width=True):
                    with st.spinner(f"Finding {mood_key} songs ..."):
                        st.session_state.search_results = search_by_mood(
                            mood_key, top_k=DEFAULT_TOP_K
                        )
                        st.session_state.last_query = f"Mood: {mood_key}"


# ── Display search results ─────────────────────────────────────
with col_search:
    if st.session_state.search_results:
        st.markdown("---")
        st.markdown(f"**Results for:** *{st.session_state.last_query}*")

        for i, song in enumerate(st.session_state.search_results):
            duration_min = song.get("duration_ms", 0) / 60000
            genre = song.get("playlist_genre", "")
            sub   = song.get("playlist_subgenre", "")
            genre_display = f"{genre} / {sub}" if sub else genre

            col_info, col_play = st.columns([5, 1])

            with col_info:
                st.markdown(f"""
                <div class="ct-card">
                    <p class="ct-title">{i+1}. {song['track_name']}</p>
                    <p class="ct-artist">{song['track_artist']}</p>
                    <p class="ct-meta">
                        {song.get('track_album_name', '')} &nbsp;•&nbsp;
                        {genre_display} &nbsp;•&nbsp;
                        {duration_min:.1f} min
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_play:
                if st.button("Play", key=f"play_{i}",
                             help=f"Play {song['track_name']}",
                             use_container_width=True):
                    success = st.session_state.player.play(song)
                    if not success:
                        st.error(st.session_state.player.error_message
                                 or "Could not load audio.")
                    st.rerun()


# ── Now Playing panel ──────────────────────────────────────────
with col_player:
    st.markdown(
        f'<div class="ct-section">{load_icon("music-note.png", 22)} Now Playing</div>',
        unsafe_allow_html=True,
    )

    player = st.session_state.player

    if player.current_song:
        song = player.current_song
        duration_str = player.format_duration(song.get("duration_ms", 0))
        np_icon = load_icon("play-buttton.png", 16)

        st.markdown(f"""
        <div class="ct-now-playing">
            <p class="ct-np-label">{np_icon} NOW PLAYING</p>
            <p class="ct-np-track">{song['track_name']}</p>
            <p class="ct-np-artist">{song['track_artist']}</p>
            <p class="ct-np-album">
                {song.get('track_album_name', 'Unknown Album')} &nbsp;•&nbsp; {duration_str}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Real audio player ──
        if player.has_audio():
            player_html = render_audio_player(
                audio_bytes=player.audio_bytes,
                title=song.get("track_name", "Unknown"),
                artist=song.get("track_artist", "Unknown"),
                album=song.get("track_album_name", ""),
                duration_str=duration_str,
            )
            components.html(player_html, height=200)
        else:
            if player.error_message:
                st.warning(player.error_message)

        # ── Clear button ──
        if st.button("Clear Track", key="ctrl_clear", use_container_width=True,
                     help="Remove the current track and stop the player"):
            player.stop()
            st.rerun()

        # ── Song details ──
        with st.expander("Song Details"):
            detail_cols = st.columns(2)
            with detail_cols[0]:
                st.metric("Energy",       f"{song.get('energy', 0):.2f}")
                st.metric("Danceability", f"{song.get('danceability', 0):.2f}")
                st.metric("Tempo",        f"{song.get('tempo', 0):.0f} BPM")
            with detail_cols[1]:
                st.metric("Valence (Happiness)", f"{song.get('valence', 0):.2f}")
                st.metric("Popularity",          f"{song.get('track_popularity', 0)}/100")
                st.metric("Genre",               song.get("playlist_genre", "N/A"))
    else:
        np_icon = load_icon("music-note.png", 28)
        st.markdown(f"""
        <div class="ct-empty">
            {np_icon}
            <p>Search for a song and hit play</p>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p class="ct-footer">'
    "CarTune — Built with Qdrant Edge, Whisper &amp; FastEmbed &nbsp;|&nbsp; "
    "All search runs locally, no cloud required"
    "</p>",
    unsafe_allow_html=True,
)
