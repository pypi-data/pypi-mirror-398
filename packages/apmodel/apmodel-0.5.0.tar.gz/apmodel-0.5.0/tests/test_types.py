from datetime import datetime, timezone

from apmodel.context import LDContext
from apmodel.core.object import Object
from apmodel.types import ActivityPubModel


def test_activity_pub_model_creation():
    obj = Object(id="http://example.com/obj", name="Test Object")

    assert obj.id == "http://example.com/obj"
    assert obj.name == "Test Object"


def test_activity_pub_model_dump():
    # Test the dump method
    obj = Object(id="http://example.com/obj", name="Test Object")

    dumped = obj.dump()

    assert "id" in dumped
    assert "name" in dumped
    assert dumped["id"] == "http://example.com/obj"
    assert dumped["name"] == "Test Object"


def test_activity_pub_model_serializer():
    obj = Object(id="http://example.com/obj", name="Test Object")

    serialized = obj.serialize_to_json_ld()

    assert "@context" in serialized
    assert "id" in serialized
    assert "name" in serialized
    assert serialized["id"] == "http://example.com/obj"
    assert serialized["name"] == "Test Object"


def test_activity_pub_model_with_nested_object():
    nested_obj = Object(id="http://example.com/nested", name="Nested Object")
    main_obj = Object(
        id="http://example.com/main",
        name="Main Object",
        attachment=[nested_obj],
    )

    serialized = main_obj.serialize_to_json_ld()

    assert "@context" in serialized
    assert "id" in serialized
    assert "name" in serialized
    assert "attachment" in serialized
    assert len(serialized["attachment"]) == 1
    assert serialized["attachment"][0]["id"] == "http://example.com/nested"
    assert serialized["attachment"][0]["name"] == "Nested Object"
    assert "@context" not in serialized["attachment"][0]


def test_activity_pub_model_context_aggregation():
    obj = Object(
        id="http://example.com/obj",
        name="Test Object",
        context=LDContext(
            [
                "https://www.w3.org/ns/activitystreams",
                "http://example.com/custom_context",
            ]
        ),
    )

    serialized = obj.serialize_to_json_ld()

    assert "@context" in serialized
    assert "https://www.w3.org/ns/activitystreams" in serialized["@context"]
    assert "http://example.com/custom_context" in serialized["@context"]


def test_activity_pub_model_extra_fields():
    raw_obj = {
        "id": "http://example.com/obj",
        "name": "Test Object",
        "customField": "custom_value",
    }

    obj = ActivityPubModel.model_validate(raw_obj)

    serialized = obj.model_dump(by_alias=True)

    assert "id" in serialized
    assert "name" in serialized
    assert "customField" in serialized
    assert serialized["customField"] == "custom_value"


def test_activity_pub_model_private_attributes():
    obj = ActivityPubModel(id="http://example.com/obj", name="Test Object")

    assert obj.model_extra

    obj.model_extra["_private_attr"] = "private_value"

    serialized = obj.serialize_to_json_ld()

    assert "_private_attr" not in serialized
    assert "privateAttr" not in serialized


def test_activity_pub_model_datetime_serialization():
    test_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    class TestModel(ActivityPubModel):
        test_date: datetime = test_datetime
        id: str = "http://example.com/test"

    test_obj = TestModel()

    serialized = test_obj.serialize_to_json_ld()

    assert "id" in serialized
