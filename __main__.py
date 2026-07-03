"""End-to-end smoke runner: ingest → preprocess → embed → index → verify."""
if __name__ == "__main__":
    from models.config import settings
    from pipelines import embed, index, ingest_entry, preprocess

    ingest_entry.main(["--sources", "data/sources.yaml"])
    preprocess.main()
    embed.main()
    index.main()

    try:
        from jose import jwt
        token = jwt.encode({"sub": "local-dev"}, settings.jwt_secret, algorithm=settings.jwt_alg)
        print("JWT:", token)
    except ImportError:
        print("(python-jose not installed; skipping JWT smoke test)")

    print("Run API: `web3rag-api` or `make api`, then POST /assist")
