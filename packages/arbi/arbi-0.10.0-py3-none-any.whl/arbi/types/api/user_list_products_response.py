# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["UserListProductsResponse", "UserListProductsResponseItem", "UserListProductsResponseItemPrice"]


class UserListProductsResponseItemPrice(BaseModel):
    """Stripe product price information."""

    amount: int

    currency: str

    interval: str

    interval_count: int

    price_id: str


class UserListProductsResponseItem(BaseModel):
    """Stripe product with pricing information."""

    name: str

    prices: List[UserListProductsResponseItemPrice]

    product_id: str

    description: Optional[str] = None


UserListProductsResponse: TypeAlias = List[UserListProductsResponseItem]
