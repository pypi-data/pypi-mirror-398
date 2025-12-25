from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class User(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__ = "users"
    __primary_key__: ClassVar[list[str]] = ["id"]

    id: int = Field(..., title="ID")
    name: str = Field(..., title="Name")
    email: str = Field(..., title="Email")
    age: int = Field(..., title="Age")
    is_active: bool = Field(default=True, title="Is Active")

