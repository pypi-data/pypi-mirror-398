from typing import Optional

from pydantic import Field

from ...core.activity import Activity


class Delete(Activity):
    type: Optional[str] = Field(default="Delete", kw_only=True, frozen=True)
