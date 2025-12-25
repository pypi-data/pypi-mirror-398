from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Dislike(Activity):
    type: Optional[str] = Field(default="Dislike", kw_only=True, frozen=True)
