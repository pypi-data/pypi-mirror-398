from typing import Optional

from foodeo_core.shared.entities.irequests import IProductsRequest, IModifierRequest, PRODUCT_TYPE_NAME


class ProductInRequest(IProductsRequest):
    request_item: Optional[int] = None
    order: Optional[int] = None

    def get_type_name(self) -> PRODUCT_TYPE_NAME:
        return PRODUCT_TYPE_NAME.REQUEST_ITEM

    def get_id(self) -> int:
        return self.request_item
