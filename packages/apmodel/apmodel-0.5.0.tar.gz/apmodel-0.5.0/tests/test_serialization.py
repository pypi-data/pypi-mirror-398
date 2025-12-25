from pathlib import Path

import pytest

import apmodel
from apmodel.context import LDContext
from apmodel.core.object import Object


@pytest.fixture
def test_data_path(request) -> Path:
    return Path(request.path.parent) / "data"


def test_basic_serialization():
    obj = Object(id="http://example.com/obj", name="Test Object")
    result = apmodel.to_dict(obj)

    assert "@context" in result
    assert result["@context"] == ["https://www.w3.org/ns/activitystreams"]
    assert result["id"] == "http://example.com/obj"
    assert result["name"] == "Test Object"
    assert "context" not in result


def test_nested_object_serialization():
    nested_obj = Object(
        id="http://example.com/nested",
        name="Nested Object",
        context=LDContext("http://example.com/nested_context"),
    )
    main_obj = Object(
        id="http://example.com/main",
        name="Main Object",
        content="Some content",
        attachment=[nested_obj],
    )

    result = apmodel.to_dict(main_obj)

    assert "@context" in result
    assert isinstance(result["@context"], list)
    assert "https://www.w3.org/ns/activitystreams" in result["@context"]
    assert "http://example.com/nested_context" in result["@context"]

    assert "attachment" in result
    assert isinstance(result["attachment"], list)
    assert len(result["attachment"]) == 1
    nested_dict = result["attachment"][0]
    assert nested_dict["id"] == "http://example.com/nested"
    assert nested_dict["name"] == "Nested Object"
    assert "@context" not in nested_dict


def test_multiple_context_types():
    ctx_dict = {"ex": "http://example.org/ns#"}
    nested_obj_1 = Object(
        id="http://example.com/n1",
        name="N1",
        context=LDContext("http://example.com/n1_ctx"),
    )
    nested_obj_2 = Object(
        id="http://example.com/n2",
        name="N2",
        context=LDContext(ctx_dict),
    )
    main_obj = Object(
        id="http://example.com/main",
        name="Main",
        context="http://example.com/main_ctx_str",
        attachment=[nested_obj_1, nested_obj_2],
    )

    result = apmodel.to_dict(main_obj)
    print(f"DEBUG(test_multiple): Final result['@context']: {result.get('@context')}")

    assert "@context" in result
    assert isinstance(result["@context"], list)
    assert "https://www.w3.org/ns/activitystreams" in result["@context"]
    assert "http://example.com/main_ctx_str" in result["@context"]
    assert "http://example.com/n1_ctx" in result["@context"]
    assert ctx_dict in result["@context"]

    assert "@context" not in result["attachment"][0]
    assert "@context" not in result["attachment"][1]


def test_no_context_object():
    obj = Object(id="http://example.com/plain", name="Plain Object")
    result = apmodel.to_dict(obj)

    assert "@context" in result
    assert result["@context"] == ["https://www.w3.org/ns/activitystreams"]
    assert result["id"] == "http://example.com/plain"
    assert "context" not in result


def test_context_list_single_item():
    obj = Object(
        id="http://example.com/single_ctx",
        context=LDContext("https://www.w3.org/ns/activitystreams"),
    )
    result = apmodel.to_dict(obj)

    assert "@context" in result
    assert result["@context"] == ["https://www.w3.org/ns/activitystreams"]
    assert result["id"] == "http://example.com/single_ctx"
