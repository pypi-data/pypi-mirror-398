from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class EmbeddingTarget(BaseModel):
    model: str | Any
    embedding_class: str | Any
    embedding_field: str
    primary_key: Optional[str] = None
    fetch_fn: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class MLConfig(BaseSettings):
    """Main ML configuration (flat fields for easy ENV overrides)."""

    model_config = SettingsConfigDict(
        env_prefix='',
        env_file='.env',
        case_sensitive=False,
        extra='ignore',
        populate_by_name=True,
    )

    async_mode: bool = True
    ml_model_class: str = 'amsdal_ml.ml_models.openai_model.OpenAIModel'
    ml_retriever_class: str = 'amsdal_ml.ml_retrievers.openai_retriever.OpenAIRetriever'
    ml_ingesting_class: str = 'amsdal_ml.ml_ingesting.openai_ingesting.OpenAIIngesting'

    llm_model_name: str = 'gpt-4o'
    llm_temperature: float = 0.0

    embed_model_name: str = 'text-embedding-3-small'
    embed_max_depth: int = 2
    embed_max_chunks: int = 10
    embed_max_tokens_per_chunk: int = 800

    retriever_default_k: int = 8
    retriever_include_tags_default: list[str] = Field(default_factory=list)
    retriever_exclude_tags_default: list[str] = Field(default_factory=list)

    openai_api_key: Optional[str] = Field(default=None, description='OPENAI_API_KEY')
    claude_api_key: Optional[str] = Field(default=None, description='ANTHROPIC_API_KEY')

    embedding_targets: list[EmbeddingTarget] = Field(default_factory=list)

    @property
    def resolved_openai_key(self) -> Optional[str]:
        return self.openai_api_key


ml_config = MLConfig()
