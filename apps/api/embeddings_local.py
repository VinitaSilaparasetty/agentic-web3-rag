from functools import lru_cache
from sentence_transformers import SentenceTransformer

@lru_cache(maxsize=1)
def _model():
    # Same model used by your pipelines.embed (dim=384)
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_query(text: str):
    # Normalized embedding for cosine similarity in Qdrant
    return _model().encode([text], normalize_embeddings=True)[0].tolist()
