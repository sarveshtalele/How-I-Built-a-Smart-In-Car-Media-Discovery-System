# CarTune: Smart In-Car Media Discovery System 🚗🎶

CarTune is a modern, offline-first music discovery platform designed specifically for in-car infotainment systems. Utilizing highly optimized local AI models, CarTune handles voice requests, natural language text searches, and intelligent mood-based discovery directly on the edge.

By moving embedding and vector search entirely off the cloud, CarTune ensures **zero latency** and **privacy-first** media discovery—essential for the next generation of smart vehicles. 

We have specifically reduced this repository to an **MVP (Minimum Viable Product)** using **Streamlit** to rapidly demonstrate and test the fundamental machine learning architecture without the bloat of external web frameworks.

## 🚀 Key Features

*   **Voice Search Generation:** Integrated seamlessly with Streamlit's `st.audio_input`, allowing drivers to make requests entirely hands-free through their dashboard mock UI.
*   **Local Transcription:** Audio is parsed entirely offline using **OpenAI Whisper** base models. No continuous internet connection to cloud LLM providers required.
*   **Vector Search & RAG:** Uses **Qdrant Edge** and **FastEmbed** (`sentence-transformers/all-MiniLM-L6-v2`) to turn song metadata, analytics, and moods into dense vectors. Finding "an energetic pop song" runs entirely in RAM.
*   **Streamlit UI Mockup:** A beautiful automobile-themed layout designed directly inside Python via `app.py`.

## 📁 System Architecture

```text
ghostwriting/
├── app.py                       # Single-file Streamlit MVP (Dashboard UI)
├── requirements.txt             # Python Package Dependencies
├── pyproject.toml               # Modern UV packaging details
├── README.md                    # Project Documentation
├── data/                        # Contains the raw CSV and the built Qdrant Edge Database Shard
└── src/                         # The core local AI machine learning logic
    ├── ingest.py                # Database embedding ingestion script
    ├── search.py                # Vector search methodology
    ├── voice.py                 # Whisper voice transcription logic
    ├── config.py                # Central app configuration
    └── player.py                # State manager for audio playback
```

## 🛠 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (Required by OpenAI Whisper for internal audio decoding)

### 2. General Setup
We recommend using `uv` for fast dependency management, but native pip works as well.
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Build the Database (Run Once)
Before searching, you need to parse the dataset (located in `data/spotify_songs.csv`) into the vector DB logic.
```bash
uv run python src/ingest.py
```
This builds the `Qdrant Edge` shard locally on disk (`data/qdrant_shard`).

### 4. Running the Interface

For the standalone Python experience running the Streamlit Dashboard:
```bash
uv run streamlit run app.py
```

Open your browser to the local network port indicated by Streamlit.

## 🧠 Model Tech Stack
*   **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` via `FastEmbed`.
*   **Vector Datastore:** `qdrant-edge-py` for pure local query and shard storage.
*   **Voice Transcription:** `openai-whisper` (Base model) processing direct Streamlit audio buffer ingestion.
