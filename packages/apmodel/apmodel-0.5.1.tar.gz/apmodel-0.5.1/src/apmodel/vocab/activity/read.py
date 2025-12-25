from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Read(Activity):
    type: Optional[str] = Field(default="Read", kw_only=True, frozen=True)
