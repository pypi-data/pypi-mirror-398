from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Like(Activity):
    type: Optional[str] = Field(default="Like", kw_only=True, frozen=True)
