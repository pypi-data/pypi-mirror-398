# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ModelCitationConfig"]


class ModelCitationConfig(BaseModel):
    max_numb_citations: Optional[int] = FieldInfo(alias="MAX_NUMB_CITATIONS", default=None)
    """Maximum number of citations to return per statement."""

    min_char_size_to_answer: Optional[int] = FieldInfo(alias="MIN_CHAR_SIZE_TO_ANSWER", default=None)
    """Minimum character length to be considered as a statement for citation."""

    sim_model_name: Optional[str] = FieldInfo(alias="SIM_MODEL_NAME", default=None)
    """Name of the model to be used."""

    sim_threashold: Optional[float] = FieldInfo(alias="SIM_THREASHOLD", default=None)
    """How similar does the statement needs to be to be considered as citation."""
