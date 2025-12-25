from typing import ClassVar

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Order(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__ = "orders"
    __primary_key__: ClassVar[list[str]] = ["id"]

    id: int = Field(..., title="ID")
    user_id: int = Field(..., title="User ID")
    product_id: int = Field(..., title="Product ID")
    quantity: int = Field(..., title="Quantity")
    order_date: str = Field(..., title="Order Date")

