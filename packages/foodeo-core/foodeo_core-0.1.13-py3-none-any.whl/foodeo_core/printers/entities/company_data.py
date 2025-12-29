from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_reason: Optional[str] = None
    company_name: Optional[str] = None
    company_dni: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
