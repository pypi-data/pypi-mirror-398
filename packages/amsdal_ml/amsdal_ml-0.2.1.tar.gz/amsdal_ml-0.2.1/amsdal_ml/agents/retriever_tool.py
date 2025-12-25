from __future__ import annotations

import logging
import sys
from typing import Any
from typing import Optional

from mcp.server.fastmcp.tools.base import Tool
from pydantic import BaseModel
from pydantic import Field

from amsdal_ml.ml_retrievers.openai_retriever import OpenAIRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('server2.log'), logging.StreamHandler(sys.stdout)],
)


class RetrieverArgs(BaseModel):
    query: str = Field(..., description='User search query')
    k: int = 5
    include_tags: Optional[list[str]] = None
    exclude_tags: Optional[list[str]] = None


class _RetrieverSingleton:
    """Singleton holder for lazy retriever initialization."""

    _instance: Optional[OpenAIRetriever] = None

    @classmethod
    def get(cls) -> OpenAIRetriever:
        """Lazy initialization of retriever to ensure env vars are loaded."""
        if cls._instance is None:
            cls._instance = OpenAIRetriever()
        return cls._instance


async def retriever_search(
    query: str = Field(..., description='User search query'),
    k: int = 5,
    include_tags: Optional[list[str]] = None,
    exclude_tags: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    logging.info(
        f'retriever_search called with query={query}, k={k}, include_tags={include_tags}, exclude_tags={exclude_tags}'
    )
    retriever = _RetrieverSingleton.get()
    chunks = await retriever.asimilarity_search(
        query=query,
        k=k,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
    )
    logging.info(f'retriever_search found {len(chunks)} chunks: {chunks}')
    out: list[dict[str, Any]] = []
    for c in chunks:
        if hasattr(c, 'model_dump'):
            out.append(c.model_dump())
        elif hasattr(c, 'dict'):
            out.append(c.dict())
        elif isinstance(c, dict):
            out.append(c)
        else:
            out.append({'raw_text': str(c)})
    return out


retriever_tool = Tool.from_function(
    retriever_search,
    name='search',
    description='Semantic search in knowledge base (OpenAI embeddings)',
    structured_output=True,
)
