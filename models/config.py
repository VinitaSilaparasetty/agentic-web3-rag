from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Qdrant aliases / collections
    qdrant_alias_active: str = "web3_docs_active"
    qdrant_alias_staging: str = "web3_docs_staging"
    qdrant_collection_active: str = "web3_docs_active"
    qdrant_collection_staging: str = "web3_docs_staging"

    # Qdrant connection
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")

    # External API credentials
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_api_url: str = Field(default="https://api.github.com", alias="GITHUB_API_URL")

    # Embedding model (must match the model used during indexing)
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )

    # Ingest settings
    user_agent: str = Field(
        default="web3-rag-bot/0.1 (+https://github.com/web3-rag/agentic-web3-rag)",
        alias="USER_AGENT",
    )
    policy_mode: str = Field(default="link-only", alias="POLICY_MODE")

    # Auth (used for local dev JWT smoke test)
    jwt_secret: str = Field(default="dev-secret-change-me", alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()

__all__ = ["Settings", "settings"]
