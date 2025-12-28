# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ..._models import BaseModel

__all__ = ["HealthRetrieveStatusResponse", "ModelsHealth", "ModelsHealthModel", "Service"]


class ModelsHealthModel(BaseModel):
    model: str

    status: str

    detail: Optional[str] = None


class ModelsHealth(BaseModel):
    application: str

    models: List[ModelsHealthModel]


class Service(BaseModel):
    name: str

    status: str

    detail: Optional[str] = None

    service_info: Optional[Dict[str, object]] = None


class HealthRetrieveStatusResponse(BaseModel):
    """
    Consolidated health response containing all system status and version information
    """

    status: str

    available_models: Optional[List[str]] = None

    backend_git_hash: Optional[str] = None

    frontend_docker_version: Optional[str] = None

    models_health: Optional[ModelsHealth] = None

    services: Optional[List[Service]] = None
