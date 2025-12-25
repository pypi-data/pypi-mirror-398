from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Reject(Activity):
    type: Optional[str] = Field(default="Reject", kw_only=True, frozen=True)


class TentativeReject(Reject):
    type: Optional[str] = Field(default="TentativeReject", kw_only=True, frozen=True)
