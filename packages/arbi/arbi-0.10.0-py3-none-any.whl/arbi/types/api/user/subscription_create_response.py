# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ...._models import BaseModel

__all__ = ["SubscriptionCreateResponse"]


class SubscriptionCreateResponse(BaseModel):
    """Response containing Stripe checkout session client secret."""

    client_secret: str
