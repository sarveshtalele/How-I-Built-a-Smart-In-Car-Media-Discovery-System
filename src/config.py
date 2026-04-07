"""
config.py — Central configuration for CarTune.

All paths, model identifiers, and search defaults live here so the rest of
the codebase only ever imports symbols from one place.
"""

import os
from pathlib import Path

# ── Project paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR  = PROJECT_ROOT / "data"
SHARD_DIR = DATA_DIR / "qdrant_shard"

# Unified metadata CSV built by scripts/prepare_dataset.py
SONGS_CSV = DATA_DIR / "songs.csv"

# Root of the FMA-small audio collection (8,000 MP3 files in XXX/ subdirs)
FMA_DIR = PROJECT_ROOT / "fma_small"

# ── Embedding settings ─────────────────────────────────────────
# We use FastEmbed's all-MiniLM-L6-v2 model — same as before, 384-dim,
# CPU-only via ONNX, perfect for an on-device Qdrant Edge shard.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384

# ── Qdrant Edge settings ───────────────────────────────────────
DISTANCE_METRIC = "Cosine"

# ── Whisper settings ───────────────────────────────────────────
WHISPER_MODEL = "small"

# ── Search defaults ────────────────────────────────────────────
DEFAULT_TOP_K = 5
