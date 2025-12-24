# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .schema import Schema
from ..._models import BaseModel

__all__ = ["DatasetPublic"]


class DatasetPublic(BaseModel):
    """Public-facing dataset schema.

    Represents the metadata of a dataset exposed via the API, including its
    unique identifier, user-provided name, row count, and column schema.
    """

    id: str

    dataset_schema: Schema

    file_size_bytes: int

    name: str

    num_rows: int
