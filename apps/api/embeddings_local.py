from functools import lru_cache

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=MODEL_ID)


def embed_query(text: str) -> list[float]:
    vectors = list(_model().embed([text]))
    return [float(x) for x in vectors[0]]
