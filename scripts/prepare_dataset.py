"""
prepare_dataset.py — Build data/songs.csv from the FMA-small MP3 collection.

The FMA dataset only ships audio files in the project — no metadata CSV is
included.  Fortunately every MP3 carries embedded ID3 tags (title, artist,
album, genre).  This script walks the fma_small/ directory, reads those tags
with mutagen, and writes a unified CSV that the ingestion pipeline can consume.

Output: data/songs.csv with columns:
    track_id, track_name, track_artist, track_album_name,
    genre, subgenre, duration_ms, popularity,
    energy, valence, danceability, tempo, audio_path

Run:
    python scripts/prepare_dataset.py
"""

from __future__ import annotations

import os
import sys
import csv
from pathlib import Path

# add project root to sys.path so we can import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

from config import FMA_DIR, SONGS_CSV, DATA_DIR


# ── helpers ────────────────────────────────────────────────────

def _safe_str(value, default: str = "") -> str:
    """Convert an ID3 frame (or anything) to a clean string."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _genre_to_mood_defaults(genre: str) -> dict:
    """
    FMA only gives us a genre tag — no audio features.
    We map the genre to plausible default mood values so the embedding
    descriptions stay informative.  These are rough heuristics, not science.
    """
    g = genre.lower() if genre else ""

    # (energy, valence, danceability, tempo)
    presets = {
        "hip-hop":      (0.75, 0.55, 0.80, 95.0),
        "electronic":   (0.80, 0.55, 0.75, 125.0),
        "electronica":  (0.75, 0.55, 0.70, 120.0),
        "rock":         (0.80, 0.50, 0.50, 130.0),
        "pop":          (0.70, 0.70, 0.70, 115.0),
        "folk":         (0.35, 0.55, 0.40, 95.0),
        "instrumental": (0.40, 0.50, 0.35, 100.0),
        "international":(0.55, 0.60, 0.55, 110.0),
        "experimental": (0.45, 0.40, 0.35, 105.0),
        "jazz":         (0.40, 0.55, 0.50, 110.0),
        "classical":    (0.30, 0.45, 0.20, 90.0),
        "blues":        (0.45, 0.45, 0.50, 100.0),
        "country":      (0.55, 0.60, 0.55, 110.0),
        "ambient":      (0.20, 0.40, 0.25, 80.0),
        "punk":         (0.90, 0.55, 0.55, 150.0),
        "metal":        (0.90, 0.40, 0.45, 140.0),
        "soul":         (0.55, 0.65, 0.65, 100.0),
        "funk":         (0.75, 0.75, 0.85, 110.0),
        "reggae":       (0.55, 0.70, 0.70, 90.0),
    }

    for key, vals in presets.items():
        if key in g:
            energy, valence, dance, tempo = vals
            return {
                "energy":       energy,
                "valence":      valence,
                "danceability": dance,
                "tempo":        tempo,
            }

    # neutral default
    return {
        "energy":       0.5,
        "valence":      0.5,
        "danceability": 0.5,
        "tempo":        120.0,
    }


def extract_track_metadata(filepath: Path) -> dict | None:
    """
    Read ID3 tags + audio info from a single MP3 file.
    Returns a dict ready for the songs.csv row, or None if the file is
    corrupt or has no usable title.
    """
    try:
        try:
            tags = ID3(filepath)
        except ID3NoHeaderError:
            tags = {}

        audio = MP3(filepath)
    except Exception as e:
        print(f"  [skip] {filepath.name}: {e}")
        return None

    title  = _safe_str(tags.get("TIT2"))
    artist = _safe_str(tags.get("TPE1"), "Unknown Artist")
    album  = _safe_str(tags.get("TALB"), "Unknown Album")
    genre  = _safe_str(tags.get("TCON"), "Unknown")

    # bail out if we have no title — those tracks are useless for search
    if not title:
        title = filepath.stem  # fall back to the filename

    # filename like "108014.mp3" → 108014
    try:
        track_id = int(filepath.stem)
    except ValueError:
        return None

    duration_ms = int(audio.info.length * 1000) if audio.info.length else 0
    if duration_ms < 5000:    # under 5 seconds = corrupt
        return None

    moods = _genre_to_mood_defaults(genre)

    rel_audio_path = filepath.relative_to(PROJECT_ROOT).as_posix()

    return {
        "track_id":         track_id,
        "track_name":       title,
        "track_artist":     artist,
        "track_album_name": album,
        "genre":            genre,
        "subgenre":         "",
        "duration_ms":      duration_ms,
        "popularity":       50,
        "energy":           moods["energy"],
        "valence":          moods["valence"],
        "danceability":     moods["danceability"],
        "tempo":            moods["tempo"],
        "audio_path":       rel_audio_path,
    }


# ── main pipeline ──────────────────────────────────────────────

def scan_fma_directory(fma_dir: Path) -> list[dict]:
    """Walk fma_small/XXX/XXXXXX.mp3 and collect metadata for every file."""
    if not fma_dir.exists():
        raise FileNotFoundError(
            f"FMA directory not found at {fma_dir}.\n"
            f"Make sure fma_small/ is unzipped at the project root."
        )

    print(f"[prep] Scanning {fma_dir} ...")

    rows: list[dict] = []
    skipped = 0
    total_seen = 0

    subdirs = sorted([d for d in fma_dir.iterdir() if d.is_dir()])
    print(f"[prep] Found {len(subdirs)} sub-directories")

    for subdir in subdirs:
        mp3_files = sorted(subdir.glob("*.mp3"))
        for mp3 in mp3_files:
            total_seen += 1

            # skip suspiciously small files (corrupt)
            if mp3.stat().st_size < 50_000:
                skipped += 1
                continue

            row = extract_track_metadata(mp3)
            if row is None:
                skipped += 1
                continue

            rows.append(row)

        if (subdirs.index(subdir) + 1) % 20 == 0:
            print(f"  ... processed {subdirs.index(subdir)+1}/{len(subdirs)} dirs, "
                  f"{len(rows)} tracks so far")

    print(f"[prep] Scan complete — {len(rows)} usable tracks "
          f"({skipped} skipped out of {total_seen})")
    return rows


def write_songs_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "track_id", "track_name", "track_artist", "track_album_name",
        "genre", "subgenre", "duration_ms", "popularity",
        "energy", "valence", "danceability", "tempo", "audio_path",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[prep] Wrote {len(rows)} rows to {output_path}")


def run() -> None:
    rows = scan_fma_directory(FMA_DIR)
    write_songs_csv(rows, SONGS_CSV)

    # quick stats
    if rows:
        genres: dict[str, int] = {}
        for r in rows:
            g = r["genre"] or "Unknown"
            genres[g] = genres.get(g, 0) + 1

        print("\n[prep] Genre distribution:")
        for g, c in sorted(genres.items(), key=lambda x: -x[1])[:15]:
            print(f"  {g:30s} {c:5d}")


if __name__ == "__main__":
    run()
