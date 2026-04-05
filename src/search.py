"""
search.py — Handles semantic search over the song library using Qdrant Edge.

Once the shard is built by ingest.py, this module loads it and lets you
query with any natural-language string.  FastEmbed encodes the query on the
fly, then Qdrant Edge does an approximate nearest-neighbor lookup in
the local shard.
"""

from fastembed import TextEmbedding
from qdrant_edge import (
    EdgeShard,
    Query,
    SearchRequest,
    Filter,
    FieldCondition,
    MatchTextAny,
)

from config import SHARD_DIR, EMBEDDING_MODEL, DEFAULT_TOP_K


# ── Module-level singletons ───────────────────────────────────
# We keep the embedding model and shard loaded in memory so repeated
# searches don't pay the startup cost every time.
_embedding_model = None
_shard = None


def _get_model():
    """Lazy-load the FastEmbed model."""
    global _embedding_model
    if _embedding_model is None:
        print("[search] Loading FastEmbed model ...")
        _embedding_model = TextEmbedding(EMBEDDING_MODEL)
    return _embedding_model


def _get_shard():
    """Lazy-load the Qdrant Edge shard from disk."""
    global _shard
    if _shard is None:
        print(f"[search] Loading Qdrant Edge shard from {SHARD_DIR} ...")
        _shard = EdgeShard.load(str(SHARD_DIR))
        info = _shard.info()
        print(f"[search] Shard loaded — {info.points_count} points indexed.")
    return _shard


def embed_query(text):
    """
    Turn a natural-language query into a 384-dim vector.
    FastEmbed's embed() returns a generator, so we grab the first
    (and only) item from it.
    """
    model = _get_model()
    vectors = list(model.embed([text]))
    return vectors[0].tolist()


def search_songs(query_text, top_k=DEFAULT_TOP_K, genre_filter=None):
    """
    Given a user's voice command (already transcribed to text), find
    the most relevant songs in the local library.

    Parameters
    ----------
    query_text : str
        Natural-language search query, e.g. "play something chill by Adele"
    top_k : int
        How many results to return.
    genre_filter : str or None
        If set, restrict results to this playlist_genre (e.g. "pop", "rock").

    Returns
    -------
    list[dict]
        Each dict has the song metadata plus a 'score' key (similarity).
    """
    shard = _get_shard()
    query_vector = embed_query(query_text)

    # Build the search request
    search_filter = None
    if genre_filter:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="playlist_genre",
                    match=MatchTextAny(text_any=genre_filter.lower()),
                )
            ]
        )

    request = SearchRequest(
        query=Query.Nearest(query_vector),
        filter=search_filter,
        limit=top_k,
        with_payload=True,
        with_vector=False,
    )

    results = shard.search(request)

    # reshape into simple dicts that the UI can consume
    songs = []
    for hit in results:
        song = dict(hit.payload)
        song["score"] = hit.score
        song["point_id"] = hit.id
        songs.append(song)

    return songs


def search_by_mood(mood, top_k=DEFAULT_TOP_K):
    """
    Convenience wrapper for mood-based queries.
    Maps common mood keywords to more descriptive search phrases so
    the embedding model has richer context to work with.
    """
    mood_map = {
        "happy": "happy upbeat cheerful song",
        "sad": "sad melancholic slow emotional song",
        "energetic": "high energy fast loud workout song",
        "chill": "calm relaxing lo-fi ambient chill song",
        "romantic": "romantic love ballad slow dance song",
        "party": "party dance club banger high energy song",
    }

    expanded = mood_map.get(mood.lower(), mood)
    return search_songs(expanded, top_k=top_k)


if __name__ == "__main__":
    # quick manual test
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "upbeat dance song"
    print(f"\nSearching for: '{query}'\n")

    results = search_songs(query, top_k=5)
    for i, song in enumerate(results, 1):
        print(f"  {i}. {song['track_name']} — {song['track_artist']}")
        print(f"     Genre: {song['playlist_genre']} | Score: {song['score']:.4f}")
        print()
