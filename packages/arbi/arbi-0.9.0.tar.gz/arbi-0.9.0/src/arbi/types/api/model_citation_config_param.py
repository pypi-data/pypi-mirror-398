# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ModelCitationConfigParam"]


class ModelCitationConfigParam(TypedDict, total=False):
    max_numb_citations: Annotated[int, PropertyInfo(alias="MAX_NUMB_CITATIONS")]
    """Maximum number of citations to return per statement."""

    min_char_size_to_answer: Annotated[int, PropertyInfo(alias="MIN_CHAR_SIZE_TO_ANSWER")]
    """Minimum character length to be considered as a statement for citation."""

    sim_model_name: Annotated[str, PropertyInfo(alias="SIM_MODEL_NAME")]
    """Name of the model to be used."""

    sim_threashold: Annotated[float, PropertyInfo(alias="SIM_THREASHOLD")]
    """How similar does the statement needs to be to be considered as citation."""
