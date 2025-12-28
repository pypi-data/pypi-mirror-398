from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIWrapper(BaseModel, Generic[T]):
    code: int
    msg: Optional[str] = None
    data: Optional[T] = None
