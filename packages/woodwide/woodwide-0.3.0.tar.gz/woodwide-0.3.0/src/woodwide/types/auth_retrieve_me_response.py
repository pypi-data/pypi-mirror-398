# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias

from pydantic import Field as FieldInfo

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = ["AuthRetrieveMeResponse", "UserResponse", "APIClientResponse"]


class UserResponse(BaseModel):
    identity_type: Literal["user"]

    username: str

    created_at: Optional[datetime] = None

    dataset_ids: Optional[List[str]] = None

    email: Optional[str] = None

    full_name: Optional[str] = None

    inference_calls: Optional[int] = None

    api_model_ids: Optional[List[str]] = FieldInfo(alias="model_ids", default=None)

    num_api_keys: Optional[int] = None

    storage_used_bytes: Optional[int] = None

    train_calls: Optional[int] = None

    wwai_credits: Optional[int] = None


class APIClientResponse(BaseModel):
    identity_type: Literal["api"]

    username: str

    created_at: Optional[datetime] = None

    dataset_ids: Optional[List[str]] = None

    api_model_ids: Optional[List[str]] = FieldInfo(alias="model_ids", default=None)


AuthRetrieveMeResponse: TypeAlias = Annotated[
    Union[UserResponse, APIClientResponse], PropertyInfo(discriminator="identity_type")
]
