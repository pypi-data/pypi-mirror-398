from typing import Optional

from pydantic import Field

from ..core.link import Link


class Hashtag(Link):
    type: Optional[str] = Field(default="Hashtag", kw_only=True, frozen=True)
