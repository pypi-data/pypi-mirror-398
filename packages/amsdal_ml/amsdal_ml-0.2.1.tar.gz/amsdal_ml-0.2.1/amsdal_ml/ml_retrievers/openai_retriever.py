from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI
from openai import OpenAI

from amsdal_ml.ml_config import ml_config
from amsdal_ml.ml_ingesting.embedders.embedder import Embedder

from .default_retriever import DefaultRetriever

DEFAULT_EMBED_MODEL = ml_config.embed_model_name


class OpenAIRetriever(DefaultRetriever):
    client: OpenAI | None = None
    aclient: AsyncOpenAI | None = None

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        embed_model: Optional[str] = None,
        embedder: Embedder | None = None,
    ):
        super().__init__(embedder=embedder)

        self.api_key = api_key or ml_config.resolved_openai_key or os.getenv('OPENAI_API_KEY')
        self.embed_model = embed_model or DEFAULT_EMBED_MODEL

        if embedder is None:
            if not self.api_key:
                msg = 'OPENAI_API_KEY is required for OpenAIRetriever'
                raise RuntimeError(msg)
            self.client = OpenAI(api_key=self.api_key)
            self.aclient = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            self.aclient = None

    def _embed_query(self, text: str) -> list[float]:
        if self.embedder is not None:
            return self.embedder.embed(text)
        if not self.client:
            msg = 'OpenAI client is not configured'
            raise RuntimeError(msg)
        resp = self.client.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding

    async def _aembed_query(self, text: str) -> list[float]:
        if self.embedder is not None:
            return await self.embedder.aembed(text)
        if not self.aclient:
            msg = 'Async OpenAI client is not configured'
            raise RuntimeError(msg)
        resp = await self.aclient.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding
