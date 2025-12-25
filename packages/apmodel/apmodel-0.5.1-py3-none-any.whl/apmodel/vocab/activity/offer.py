from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Offer(Activity):
    type: Optional[str] = Field(default="Offer", kw_only=True, frozen=True)
