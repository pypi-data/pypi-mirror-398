from typing import Any

from amsdal_models.classes.fields.vector import VectorField
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic import Field


class EmbeddingModel(Model):
    __module_type__ = ModuleType.CONTRIB
    __table_name__ = 'embedding_model'

    data_object_class: str = Field(..., title='Linked object class')
    data_object_id: str = Field(..., title='Linked object ID')

    chunk_index: int = Field(..., title='Chunk index')
    raw_text: str = Field(..., title='Raw text used for embedding')

    embedding: VectorField(1536)  # type: ignore[valid-type]
    tags: list[str] = Field(default_factory=list, title='Embedding tags')
    ml_metadata: Any = Field(default=None, title='ML metadata')
