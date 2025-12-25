from __future__ import annotations

import os

from openai import AsyncOpenAI
from openai import OpenAI

from amsdal_ml.ml_config import ml_config
from amsdal_ml.ml_ingesting.embedders.embedder import Embedder

DEFAULT_EMBED_MODEL = ml_config.embed_model_name


class OpenAIEmbedder(Embedder):
    def __init__(self, *, api_key: str | None = None, embed_model: str | None = None) -> None:
        self.api_key = api_key or ml_config.resolved_openai_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            msg = 'OPENAI_API_KEY is required for OpenAIEmbedder'
            raise RuntimeError(msg)
        self.embed_model = embed_model or DEFAULT_EMBED_MODEL
        self.client = OpenAI(api_key=self.api_key)
        self.aclient = AsyncOpenAI(api_key=self.api_key)

    def embed(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding

    async def aembed(self, text: str) -> list[float]:
        resp = await self.aclient.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding
