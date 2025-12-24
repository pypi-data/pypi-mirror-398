# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["HealthCheckModelsResponse", "Model"]


class Model(BaseModel):
    model: str

    status: str

    detail: Optional[str] = None


class HealthCheckModelsResponse(BaseModel):
    application: str

    models: List[Model]
