from typing import Optional

from pydantic import Field

from ...core.activity import IntransitiveActivity


class Arrive(IntransitiveActivity):
    type: Optional[str] = Field(default="Arrive", kw_only=True, frozen=True)
