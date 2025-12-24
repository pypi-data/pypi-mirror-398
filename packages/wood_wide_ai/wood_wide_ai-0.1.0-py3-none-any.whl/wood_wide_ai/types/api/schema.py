# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["Schema", "Column"]


class Column(BaseModel):
    name: str

    type: str

    values: Optional[List[object]] = None


class Schema(BaseModel):
    columns: List[Column]
