from typing import Optional

from pydantic import Field

from ..core.object import Object


class Emoji(Object):
    type: Optional[str] = Field(default="Emoji", kw_only=True, frozen=True)
