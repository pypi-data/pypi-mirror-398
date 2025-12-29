from typing import Optional

from foodeo_core.shared.entities import LocalRequest
from foodeo_core.shared.entities.irequests import IProductsRequest, PRODUCT_TYPE_NAME


class ProductsInCorrections(IProductsRequest):
    qty: int
    order: Optional[int] = None

    def get_id(self) -> int:
        return self.request_item

    def get_type_name(self) -> PRODUCT_TYPE_NAME:
        return PRODUCT_TYPE_NAME.REQUEST_ITEM


class CorrectionLocalRequest(LocalRequest):
    products: list[ProductsInCorrections]
