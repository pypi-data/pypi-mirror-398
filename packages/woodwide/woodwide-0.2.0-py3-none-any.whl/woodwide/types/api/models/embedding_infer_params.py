# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["EmbeddingInferParams"]


class EmbeddingInferParams(TypedDict, total=False):
    dataset_id: Optional[str]

    dataset_name: Optional[str]

    model_name: Optional[str]

    coerce_schema: bool
