from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Announce(Activity):
    type: Optional[str] = Field(default="Announce", kw_only=True, frozen=True)
