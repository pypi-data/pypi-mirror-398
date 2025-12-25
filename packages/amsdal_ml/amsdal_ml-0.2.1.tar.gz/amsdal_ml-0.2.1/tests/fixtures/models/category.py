from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Category(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__ = "categories"
    __primary_key__: ClassVar[list[str]] = ["id"]

    id: int = Field(..., title="ID")
    name: str = Field(..., title="Name")
    description: str = Field(..., title="Description")

