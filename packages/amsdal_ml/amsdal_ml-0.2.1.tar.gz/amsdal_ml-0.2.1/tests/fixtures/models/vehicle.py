from typing import ClassVar
from typing import Literal

from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Vehicle(Model):
    __module_type__: ClassVar[ModuleType] = ModuleType.USER
    __table_name__ = "vehicles"
    __primary_key__: ClassVar[list[str]] = ["id"]

    id: int = Field(..., title="ID")
    make: str = Field(..., title="Make")
    model: str = Field(..., title="Model")
    year: int = Field(..., title="Year")
    engine_type: Literal["gasoline", "diesel", "electric", "hybrid"] = Field(..., title="Engine Type")
    fuel_efficiency: float | None = Field(None, title="Fuel Efficiency")
    features: list[str] = Field(default_factory=list, title="Features")
    specs: dict[str, str] | None = Field(None, title="Specifications")
    is_available: bool = Field(default=True, title="Is Available")
    price: float | None = Field(None, title="Price")
    warranty_years: int | None = Field(None, title="Warranty Years")
    maintenance_schedule: dict[str, dict[str, str]] | None = Field(
        None, title="Maintenance Schedule by Mileage"
    )
    safety_ratings: dict[str, int] | None = Field(None, title="Safety Ratings")
    options: list[Literal["navigation", "leather_seats", "sunroof", "backup_camera"]] = Field(
        default_factory=list, title="Options"
    )

