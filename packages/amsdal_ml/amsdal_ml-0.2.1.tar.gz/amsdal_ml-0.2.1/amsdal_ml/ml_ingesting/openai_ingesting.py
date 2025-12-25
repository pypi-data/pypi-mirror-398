from __future__ import annotations

import os

from openai import AsyncOpenAI
from openai import OpenAI

from amsdal_ml.ml_config import ml_config

from .default_ingesting import DefaultIngesting

DEFAULT_EMBED_MODEL = ml_config.embed_model_name


class OpenAIIngesting(DefaultIngesting):
    def __init__(self, *, api_key: str | None = None, embed_model: str = DEFAULT_EMBED_MODEL, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            msg = 'OPENAI_API_KEY is required'
            raise RuntimeError(msg)
        self.client = OpenAI(api_key=self.api_key)
        self.aclient = AsyncOpenAI(api_key=self.api_key)
        self.embed_model = embed_model

    def _embed_sync(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding

    async def _embed_async(self, text: str) -> list[float]:
        resp = await self.aclient.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding

    def generate_embeddings(self, instance, embed_func=None):
        return super().generate_embeddings(instance, embed_func or self._embed_sync)

    async def agenerate_embeddings(self, instance, embed_func=None):
        return await super().agenerate_embeddings(instance, embed_func or self._embed_async)
