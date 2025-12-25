# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = ["PredictionTrainParams"]


class PredictionTrainParams(TypedDict, total=False):
    label_column: Required[Optional[str]]

    model_name: Required[str]

    dataset_id: Optional[str]

    dataset_name: Optional[str]

    hyperparameters: Optional[str]

    input_columns: Optional[SequenceNotStr[str]]

    overwrite: bool
