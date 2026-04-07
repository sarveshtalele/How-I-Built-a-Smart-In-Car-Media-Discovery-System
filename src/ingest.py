"""
ingest.py — Loads the FMA dataset metadata, builds text descriptions for
each track, generates embeddings with FastEmbed, and stores everything in a
Qdrant Edge shard.

This is the offline indexing step.  Run it once after preparing data/songs.csv
with scripts/prepare_dataset.py.

    python -m src.ingest
"""

import os
import shutil
import time

import pandas as pd
from fastembed import TextEmbedding
from qdrant_edge import (
    CountRequest,
    Distance,
    EdgeConfig,
    EdgeShard,
    EdgeVectorParams,
    Point,
    UpdateOperation,
)

from config import (
    SONGS_CSV,
    SHARD_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    DEFAULT_TOP_K,
)


# ── helpers ────────────────────────────────────────────────────

def build_song_description(row):
    """
    Combine the most useful metadata fields into a single natural-language
    string.  This is what we embed — not the raw audio features.

    Example output:
        "Food by AWOL from the album AWOL - A Way Of Life. Genre: Hip-Hop.
         Mood: energetic, danceable."
    """
    name   = str(row.get("track_name", "")).strip()
    artist = str(row.get("track_artist", "")).strip()
    album  = str(row.get("track_album_name", "")).strip()
    genre  = str(row.get("genre", "")).strip()
    sub    = str(row.get("subgenre", "")).strip()

    energy_val  = float(row.get("energy", 0.5) or 0.5)
    valence_val = float(row.get("valence", 0.5) or 0.5)
    dance_val   = float(row.get("danceability", 0.5) or 0.5)

    mood_words = []
    if energy_val > 0.7:
        mood_words.append("energetic")
    elif energy_val < 0.3:
        mood_words.append("calm")

    if valence_val > 0.7:
        mood_words.append("happy")
    elif valence_val < 0.3:
        mood_words.append("melancholic")

    if dance_val > 0.7:
        mood_words.append("danceable")

    mood_str = ", ".join(mood_words) if mood_words else "moderate tempo"

    genre_str = genre if not sub else f"{genre}, {sub}"

    description = (
        f"{name} by {artist} from the album {album}. "
        f"Genre: {genre_str}. "
        f"Mood: {mood_str}."
    )
    return description


def load_and_clean_dataset(csv_path=SONGS_CSV):
    """
    Read the unified songs.csv produced by scripts/prepare_dataset.py
    and drop rows with missing track names or artists.
    """
    print(f"[ingest] Reading dataset from {csv_path} ...")
    df = pd.read_csv(csv_path)
    original_count = len(df)

    df = df.dropna(subset=["track_name", "track_artist"])
    df = df.drop_duplicates(subset=["track_id"], keep="first")
    df = df.reset_index(drop=True)

    print(f"[ingest] Loaded {original_count} rows, "
          f"{len(df)} unique tracks after cleanup.")
    return df


def generate_embeddings(descriptions, model_name=EMBEDDING_MODEL):
    """
    Use FastEmbed to encode every song description into a 384-dim dense vector.
    Runs on CPU via ONNX — no GPU required.
    """
    print(f"[ingest] Initialising FastEmbed model: {model_name}")
    model = TextEmbedding(model_name=model_name)

    print(f"[ingest] Generating embeddings for {len(descriptions)} tracks ...")
    start = time.time()
    embeddings = list(model.embed(descriptions))
    elapsed = time.time() - start
    print(f"[ingest] Embedding done in {elapsed:.1f}s "
          f"({len(descriptions)/elapsed:.0f} tracks/sec)")

    return embeddings


def create_shard(shard_path=SHARD_DIR, dim=EMBEDDING_DIM):
    """
    Initialise a fresh Qdrant Edge shard on disk.
    Wipes any existing shard at the same path so re-runs always start clean.
    """
    if os.path.exists(shard_path):
        print(f"[ingest] Removing old shard at {shard_path}")
        shutil.rmtree(shard_path)

    os.makedirs(shard_path, exist_ok=True)

    config = EdgeConfig(
        vectors=EdgeVectorParams(size=dim, distance=Distance.Cosine),
    )
    shard = EdgeShard.create(str(shard_path), config)
    print(f"[ingest] Created new Qdrant Edge shard at {shard_path}")
    return shard


def index_songs(shard, df, embeddings, batch_size=500):
    """
    Push every song into the Qdrant Edge shard in batches.

    The payload now includes `audio_path` so the player can stream the
    actual MP3 file straight from disk on click.
    """
    total = len(df)
    print(f"[ingest] Indexing {total} songs into Qdrant Edge ...")

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        points = []

        for idx in range(batch_start, batch_end):
            row = df.iloc[idx]
            vector = embeddings[idx].tolist() if hasattr(embeddings[idx], "tolist") else list(embeddings[idx])

            payload = {
                "track_id":          str(row["track_id"]),
                "track_name":        str(row["track_name"]),
                "track_artist":      str(row["track_artist"]),
                "track_album_name":  str(row.get("track_album_name", "")),
                "playlist_genre":    str(row.get("genre", "")),
                "playlist_subgenre": str(row.get("subgenre", "")),
                "track_popularity":  int(row.get("popularity", 50) or 50),
                "energy":            float(row.get("energy", 0.5) or 0.5),
                "valence":           float(row.get("valence", 0.5) or 0.5),
                "danceability":      float(row.get("danceability", 0.5) or 0.5),
                "tempo":             float(row.get("tempo", 120.0) or 120.0),
                "duration_ms":       int(row.get("duration_ms", 0) or 0),
                "audio_path":        str(row.get("audio_path", "")),
            }

            points.append(Point(idx, vector, payload))

        shard.update(UpdateOperation.upsert_points(points))

        done = batch_end
        print(f"  ... indexed {done}/{total} tracks")

    shard.flush()
    total_indexed = shard.count(CountRequest(exact=True))
    print(f"[ingest] Indexing complete.  Shard has {total_indexed} points.")


def run_ingestion():
    """Top-level function that orchestrates the full pipeline."""
    df = load_and_clean_dataset()
    descriptions = [build_song_description(row) for _, row in df.iterrows()]

    embeddings = generate_embeddings(descriptions)

    shard = create_shard()
    index_songs(shard, df, embeddings)


if __name__ == "__main__":
    run_ingestion()
