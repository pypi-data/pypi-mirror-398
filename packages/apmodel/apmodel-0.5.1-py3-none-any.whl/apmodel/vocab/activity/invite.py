from typing import Optional

from pydantic import Field

from .offer import Offer


class Invite(Offer):
    type: Optional[str] = Field(default="Invite", kw_only=True, frozen=True)
