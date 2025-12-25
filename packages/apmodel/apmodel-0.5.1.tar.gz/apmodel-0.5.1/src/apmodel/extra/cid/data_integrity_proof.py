from datetime import datetime, timezone
from typing import Optional

from pydantic import Field, field_serializer, field_validator

from ...context import LDContext
from ...types import ActivityPubModel


class DataIntegrityProof(ActivityPubModel):
    context: LDContext = Field(
        default_factory=lambda: LDContext(
            [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/data-integrity/v1",
            ]
        ),
        kw_only=True,
        alias="@context",
    )

    type: Optional[str] = Field(default="DataIntegrityProof", kw_only=True)
    cryptosuite: str
    proof_value: str
    proof_purpose: str
    verification_method: str
    created: str | datetime

    @field_validator("created", mode="before")
    @classmethod
    def convert_created_to_datetime(cls, v: str | datetime) -> datetime:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        if isinstance(v, datetime):
            return v
        raise ValueError("created must be a string or a datetime object")

    @field_serializer("created")
    def serialize_created_to_iso_z(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        time_formatted = dt.astimezone(timezone.utc).isoformat(timespec="seconds")

        if time_formatted.endswith("+00:00"):
            return time_formatted.replace("+00:00", "Z")

        if time_formatted.endswith("Z"):
            return time_formatted

        return time_formatted + "Z"
