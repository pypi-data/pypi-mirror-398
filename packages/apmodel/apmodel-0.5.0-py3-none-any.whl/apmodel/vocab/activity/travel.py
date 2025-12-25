from typing import Optional

from pydantic import Field

from ...core.activity import IntransitiveActivity


class Travel(IntransitiveActivity):
    type: Optional[str] = Field(default="Travel", kw_only=True, frozen=True)
