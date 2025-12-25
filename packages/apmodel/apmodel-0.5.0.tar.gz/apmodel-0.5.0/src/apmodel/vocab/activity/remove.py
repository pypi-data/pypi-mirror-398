from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Remove(Activity):
    type: Optional[str] = Field(default="Remove", kw_only=True, frozen=True)
