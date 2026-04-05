"""
ingest.py — Loads the Spotify dataset, builds text descriptions for each track,
generates embeddings with FastEmbed, and stores everything in a Qdrant Edge shard.

This is the offline indexing step.  In a real car system you'd do this once
(maybe at the factory, or when the user syncs their library over Wi-Fi)
and then ship the shard file to the vehicle's SSD.
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
    CSV_PATH,
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

    The idea is: when a driver says "play something upbeat by Drake",
    we want the description to contain both the artist name and words
    like "energetic" so the semantic search can match it.
    """
    name = str(row.get("track_name", "")).strip()
    artist = str(row.get("track_artist", "")).strip()
    album = str(row.get("track_album_name", "")).strip()
    genre = str(row.get("playlist_genre", "")).strip()
    subgenre = str(row.get("playlist_subgenre", "")).strip()

    # turn the numeric audio features into human-readable descriptors
    energy_val = row.get("energy", 0.5)
    valence_val = row.get("valence", 0.5)
    dance_val = row.get("danceability", 0.5)

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

    description = (
        f"{name} by {artist} from the album {album}. "
        f"Genre: {genre}, {subgenre}. "
        f"Mood: {mood_str}."
    )
    return description


def load_and_clean_dataset(csv_path=CSV_PATH):
    """
    Read the Spotify CSV and drop rows with missing track names.
    We also deduplicate on track_id because the same song can appear
    in multiple playlists in this dataset.
    """
    print(f"[ingest] Reading dataset from {csv_path} ...")
    df = pd.read_csv(csv_path)
    original_count = len(df)

    df = df.dropna(subset=["track_name", "track_artist"])
    df = df.drop_duplicates(subset=["track_id"], keep="first")
    df = df.reset_index(drop=True)

    print(f"[ingest] Loaded {original_count} rows, {len(df)} unique tracks after cleanup.")
    return df


def generate_embeddings(descriptions, model_name=EMBEDDING_MODEL):
    """
    Use FastEmbed to encode every song description into a dense vector.
    FastEmbed runs the model on CPU with ONNX, no GPU required — perfect
    for an edge pre-processing step.
    """
    print(f"[ingest] Initialising FastEmbed model: {model_name}")
    model = TextEmbedding(model_name=model_name)

    print(f"[ingest] Generating embeddings for {len(descriptions)} tracks ...")
    start = time.time()
    # FastEmbed returns a generator, materialise it into a list of lists
    embeddings = list(model.embed(descriptions))
    elapsed = time.time() - start
    print(f"[ingest] Embedding done in {elapsed:.1f}s ({len(descriptions)/elapsed:.0f} tracks/sec)")

    return embeddings


def create_shard(shard_path=SHARD_DIR, dim=EMBEDDING_DIM):
    """
    Initialise a fresh Qdrant Edge shard on disk.
    If one already exists at this path, we delete it and start over.
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
    Push all songs into the Qdrant Edge shard in batches.
    Each point carries the embedding as its vector and the song metadata
    as payload so we can display it in the UI later without a separate lookup.
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
                "track_id": str(row["track_id"]),
                "track_name": str(row["track_name"]),
                "track_artist": str(row["track_artist"]),
                "track_album_name": str(row.get("track_album_name", "")),
                "playlist_genre": str(row.get("playlist_genre", "")),
                "playlist_subgenre": str(row.get("playlist_subgenre", "")),
                "track_popularity": int(row.get("track_popularity", 0)),
                "energy": float(row.get("energy", 0)),
                "valence": float(row.get("valence", 0)),
                "danceability": float(row.get("danceability", 0)),
                "tempo": float(row.get("tempo", 0)),
                "duration_ms": int(row.get("duration_ms", 0)),
            }

            points.append(Point(idx, vector, payload))

        shard.update(UpdateOperation.upsert_points(points))

        done = batch_end
        print(f"  ... indexed {done}/{total} tracks")

    # flush to make sure everything is written to disk
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
