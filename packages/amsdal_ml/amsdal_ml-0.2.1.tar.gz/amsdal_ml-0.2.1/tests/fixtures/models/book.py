from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Book(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__ = 'books'
    __primary_key__: ClassVar[list[str]] = ['id']

    id: int = Field(..., title='ID')
    title: str = Field(..., title='Title')
    author_id: int = Field(..., title='Author ID')
    published_year: int = Field(..., title='Published Year')
