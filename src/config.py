import os
from pathlib import Path

# ── Project paths 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SHARD_DIR = DATA_DIR / "qdrant_shard"
CSV_PATH = DATA_DIR / "spotify_songs.csv"

# ── Embedding settings 

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ── Qdrant Edge settings 

DISTANCE_METRIC = "Cosine"

# ── Whisper settings 
WHISPER_MODEL = "small"

# ── Search defaults 
DEFAULT_TOP_K = 5
