from typing import Optional

from foodeo_core.shared.entities.irequests import IProductsRequest, IModifierRequest, PRODUCT_TYPE_NAME


class ProductInCommand(IProductsRequest):
    request_table: Optional[int] = None

    def get_type_name(self) -> PRODUCT_TYPE_NAME:
        return PRODUCT_TYPE_NAME.REQUEST_TABLE

    def get_id(self) -> int:
        return self.request_table
