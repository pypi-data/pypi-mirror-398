from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Ignore(Activity):
    type: Optional[str] = Field(default="Ignore", kw_only=True, frozen=True)
