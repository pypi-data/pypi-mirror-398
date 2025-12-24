# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .schema import Schema
from ..._models import BaseModel

__all__ = ["ModelPublic"]


class ModelPublic(BaseModel):
    """Public-facing model schema.

    Represents the metadata of a machine learning model exposed via the API.
    """

    id: str

    created_at: datetime

    name: str

    training_status: str

    type: str

    updated_at: datetime

    input_schema: Optional[Schema] = None

    label_schema: Optional[Schema] = None
