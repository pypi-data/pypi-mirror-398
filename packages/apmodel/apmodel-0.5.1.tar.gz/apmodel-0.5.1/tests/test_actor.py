from apmodel.core.collection import OrderedCollection
from apmodel.vocab.actor import (
    Actor,
    Application,
    Group,
    Organization,
    Person,
    Service,
)


def test_actor_creation():
    # Test creating an Actor instance
    actor = Actor(id="https://example.com/actor/1", name="Test Actor")

    assert actor.id == "https://example.com/actor/1"
    assert actor.name == "Test Actor"


def test_actor_subtypes():
    # Test creating different actor subtypes
    person = Person(id="https://example.com/person/1", name="Test Person")
    application = Application(id="https://example.com/app/1", name="Test App")
    group = Group(id="https://example.com/group/1", name="Test Group")
    organization = Organization(id="https://example.com/org/1", name="Test Org")
    service = Service(id="https://example.com/service/1", name="Test Service")

    assert person.type == "Person"
    assert application.type == "Application"
    assert group.type == "Group"
    assert organization.type == "Organization"
    assert service.type == "Service"


def test_actor_with_collections():
    # Test creating an Actor with collection fields
    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        inbox="https://example.com/actor/1/inbox",
        outbox="https://example.com/actor/1/outbox",
        followers="https://example.com/actor/1/followers",
    )

    assert actor.id == "https://example.com/actor/1"
    assert actor.name == "Test Actor"
    assert actor.inbox == "https://example.com/actor/1/inbox"
    assert actor.outbox == "https://example.com/actor/1/outbox"
    assert actor.followers == "https://example.com/actor/1/followers"


def test_actor_with_ordered_collections():
    # Test creating an Actor with OrderedCollection fields
    inbox_collection = OrderedCollection(id="https://example.com/actor/1/inbox")
    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        inbox=inbox_collection,
    )

    assert actor.id == "https://example.com/actor/1"
    assert actor.name == "Test Actor"
    assert actor.inbox is not None
    assert hasattr(actor.inbox, "id")


def test_actor_with_additional_properties():
    # Test creating an Actor with additional properties
    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        preferred_username="testuser",
        discoverable=True,
        indexable=False,
    )

    assert actor.id == "https://example.com/actor/1"
    assert actor.name == "Test Actor"
    assert actor.preferred_username == "testuser"
    assert actor.discoverable is True
    assert actor.indexable is False


def test_actor_serialization():
    # Test serialization of an Actor
    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        preferred_username="testuser",
        inbox="https://example.com/actor/1/inbox",
    )

    serialized = actor.model_dump(by_alias=True)

    assert serialized["id"] == "https://example.com/actor/1"
    assert serialized["name"] == "Test Actor"
    assert serialized["preferredUsername"] == "testuser"
    assert serialized["inbox"] == "https://example.com/actor/1/inbox"


def test_actor_context_inference():
    # Test that actor context inference works properly
    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        public_key=None,  # This should not trigger security context
    )

    # Call the _inference_context method to ensure it works
    result = {"id": "https://example.com/actor/1", "name": "Test Actor"}
    inferred_result = actor._inference_context(result)

    # The result should have the basic context
    assert "@context" in inferred_result
    assert "https://www.w3.org/ns/activitystreams" in inferred_result["@context"]


def test_actor_get_key():
    from apmodel.extra.cid import Multikey
    from apmodel.extra.security import CryptographicKey

    pub_key = CryptographicKey(
        id="https://example.com/actor/1#main-key",
        owner="https://example.com/actor/1",
        public_key_pem="-----BEGIN PUBLIC KEY-----\nMIIBI...IDAQAB\n-----END PUBLIC KEY-----\n",
    )
    multi_key = Multikey(
        id="https://example.com/actor/1#multi-key",
        controller="https://example.com/actor/1",
        public_key_multibase="z6Mke...e6d3",
    )

    actor = Actor(
        id="https://example.com/actor/1",
        name="Test Actor",
        public_key=pub_key,
        assertion_method=[multi_key],
    )

    # Test keys property
    assert len(actor.keys) == 2
    assert pub_key in actor.keys
    assert multi_key in actor.keys

    # Test get_key method
    assert actor.get_key("https://example.com/actor/1#main-key") == pub_key
    assert actor.get_key("https://example.com/actor/1#multi-key") == multi_key
    assert actor.get_key("non-existent-key") is None
