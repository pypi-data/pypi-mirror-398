from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Accept(Activity):
    type: Optional[str] = Field(default="Accept", kw_only=True, frozen=True)


class TentativeAccept(Accept):
    type: Optional[str] = Field(default="TentativeAccept", kw_only=True, frozen=True)
