from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Follow(Activity):
    type: Optional[str] = Field(default="Follow", kw_only=True, frozen=True)
