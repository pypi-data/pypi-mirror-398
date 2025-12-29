from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import FiskalyCountryCodes, FiskalyTerritories


class FiskalySettings(BaseModel):
    name: str
    address: str
    zip: str
    town: str
    state: Optional[str]
    country_code: FiskalyCountryCodes = Field(default=FiskalyCountryCodes.ESP)
    legal_name: str
    tax_number: str
    territory: FiskalyTerritories = Field(default=FiskalyTerritories.SPAIN_OTHER)
