from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Add(Activity):
    type: Optional[str] = Field(default="Add", kw_only=True, frozen=True)
