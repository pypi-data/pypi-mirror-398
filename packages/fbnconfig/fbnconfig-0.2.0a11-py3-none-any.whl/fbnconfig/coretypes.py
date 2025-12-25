# Types used across multiple resources which do not depend on any other resource types
from __future__ import annotations

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, PlainSerializer


class ResourceId(BaseModel):
    scope: str
    code: str


def des_isodate(value: str | dt.datetime) -> dt.datetime:
    """Deserialize ISO 8601 date string to datetime object."""
    if isinstance(value, dt.datetime):
        return value.astimezone(tz=dt.timezone.utc)
    return dt.datetime.fromisoformat(value)


def ser_isodate(value: dt.datetime) -> str:
    """Serialize datetime object to ISO 8601 string."""
    return value.isoformat()


IsoDateTime = Annotated[
    dt.datetime | dt.date,
    BeforeValidator(des_isodate), PlainSerializer(ser_isodate)
]
