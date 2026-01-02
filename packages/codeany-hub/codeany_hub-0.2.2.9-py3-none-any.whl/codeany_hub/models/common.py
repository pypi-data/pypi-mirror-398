"""Shared base models and type aliases."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TolerantModel(BaseModel):
    """Pydantic base class configured for forward compatibility."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


ISODateTime = Annotated[datetime, Field(serialization_alias="iso_datetime")]
