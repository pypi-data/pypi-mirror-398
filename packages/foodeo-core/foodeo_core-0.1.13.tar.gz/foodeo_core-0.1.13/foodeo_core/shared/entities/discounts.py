from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo

from foodeo_core.shared.enums import DiscountEnum


class DiscountBase(BaseModel):
    type: DiscountEnum = Field(...)
    value: float | int = Field(..., gte=0)


class DiscountPromotionModel(DiscountBase):
    model_config = ConfigDict(use_enum_values=True)

    @field_validator("value")
    @classmethod
    def _validate_value(cls, value: float | int, info: ValidationInfo) -> float | int:
        if "type" in info.data:
            match info.data["type"]:
                case DiscountEnum.percentage:
                    assert value <= 100, "The value must be greater than 0 and less and equal to 100."
                case DiscountEnum.numeric:
                    pass

        return value


class Discount(DiscountBase):
    model_config = ConfigDict(use_enum_values=True)

    global_discount: bool = Field(default=False, alias="all_discounted")

    @field_validator("value")
    @classmethod
    def _validate_value(cls, value: float | int, info: ValidationInfo) -> float | int:
        if "type" in info.data:
            match info.data["type"]:
                case DiscountEnum.percentage:
                    assert value <= 100, "The value must be greater than 0 and less and equal to 100."
                case DiscountEnum.numeric:
                    pass

        return value
