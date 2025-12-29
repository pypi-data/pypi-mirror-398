from decimal import Decimal

from pydantic import BaseModel, condecimal, Field, field_serializer

MonetaryField = condecimal(max_digits=10, decimal_places=2)


class IVAData(BaseModel):
    iva: MonetaryField = Field(...)
    total_imp: MonetaryField = Field(...)
    base_imp: MonetaryField = Field(...)

    class ConfigDict:
        populate_by_name = True

    @field_serializer("iva", "total_imp", "base_imp")
    def monetary_field_serializer(self, value: Decimal) -> float:
        return float(value)
