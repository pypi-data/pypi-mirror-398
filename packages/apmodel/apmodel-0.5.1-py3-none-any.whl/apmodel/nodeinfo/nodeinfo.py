from __future__ import annotations

from typing import ClassVar, List, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)
from pydantic.alias_generators import to_camel
from typing_extensions import TypeAlias

NodeinfoProtocol: TypeAlias = Literal[
    "activitypub",
    "buddycloud",
    "dfrn",
    "diaspora",
    "libertree",
    "ostatus",
    "pumpio",
    "tent",
    "xmpp",
    "zot",
]


NodeinfoInbound: TypeAlias = Literal[
    "atom1.0",
    "gnusocial",
    "imap",
    "pnut",
    "pop3",
    "pumpio",
    "rss2.0",
    "twitter",
]

NodeinfoOutbound: TypeAlias = Literal[
    "atom1.0",
    "gnusocial",
    "blogger",
    "diaspora",
    "buddycloud",
    "dreamwidth",
    "drupal",
    "facebook",
    "friendica",
    "google",
    "insanejournal",
    "libertree",
    "linkedin",
    "livejournal",
    "mediagoblin",
    "myspace",
    "pinterest",
    "pnut",
    "posterous",
    "pumpio",
    "redmatrix",
    "rss2.0",
    "smtp",
    "tent",
    "tumblr",
    "twitter",
    "wordpress",
    "xmpp",
]


class NodeinfoServices(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )

    inbound: List[NodeinfoInbound] = Field(kw_only=True)
    outbound: List[NodeinfoOutbound] = Field(kw_only=True)


class NodeinfoUsageUsers(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )

    total: Optional[int] = Field(default=None)
    active_half_year: Optional[int] = Field(default=None)
    active_month: Optional[int] = Field(default=None)


class NodeinfoUsage(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )

    users: NodeinfoUsageUsers
    local_posts: Optional[int] = Field(default=None)
    local_comments: Optional[int] = Field(default=None)


class NodeinfoSoftware(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )

    name: Optional[str] = Field(default=None, pattern=r"^[a-z0-9-]+$")
    version: Optional[str] = Field(default=None)
    repository: Optional[str] = Field(default=None)
    homepage: Optional[str] = Field(default=None)


class Nodeinfo(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )

    version: Literal["2.0", "2.1"]
    software: NodeinfoSoftware
    protocols: List[NodeinfoProtocol | str]
    services: NodeinfoServices
    open_registrations: bool
    usage: NodeinfoUsage
    metadata: dict

    _DETECTION_KEYS: ClassVar[List[str]] = [
        "version",
        "software",
        "protocols",
        "services",
        "openRegistrations",
        "usage",
        "metadata",
    ]

    @classmethod
    def is_nodeinfo_data(cls, data: dict) -> bool:
        """
        Checks if the given dictionary data matches Nodeinfo detection criteria.
        """
        return all(key in data for key in cls._DETECTION_KEYS)

    @model_serializer(mode="wrap")
    def serialize(self, handler: SerializerFunctionWrapHandler) -> dict:
        serialized = handler(self)
        if serialized["version"] == "2.0":
            if "repository" in serialized["software"]:
                serialized["software"].pop("repository")
            if "homepage" in serialized["software"]:
                serialized["software"].pop("homepage")
        return serialized

    @model_validator(mode="after")
    def validate_nodeinfo(self):
        if self.version == "2.0":
            if self.software.repository:
                self.software.repository = None
            if self.software.homepage:
                self.software.homepage = None
        return self
