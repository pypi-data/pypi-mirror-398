from datetime import datetime

from apmodel.core.object import Object
from apmodel.vocab.activity import Question


def test_question_creation():
    question = Question(id="http://example.com/question/1", name="Test Question")

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    assert question.type == "Question"


def test_question_with_one_of():
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        one_of="Option A",
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    assert question.one_of == "Option A"


def test_question_with_any_of():
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        any_of="Option B",
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    assert question.any_of == "Option B"


def test_question_with_closed():
    question = Question(
        id="http://example.com/question/1", name="Test Question", closed=True
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    assert question.closed is True


def test_question_with_datetime_closed():
    dt = datetime(2023, 1, 1, 12, 0, 0)
    question = Question(
        id="http://example.com/question/1", name="Test Question", closed=dt
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    assert question.closed == dt


def test_question_serialization_with_datetime():
    # Test serialization of a Question with datetime closed field
    dt = datetime(2023, 1, 1, 12, 0, 0)
    question = Question(
        id="http://example.com/question/1", name="Test Question", closed=dt
    )

    serialized = question.model_dump(by_alias=True)

    assert "id" in serialized
    assert "name" in serialized
    assert "closed" in serialized
    # The datetime should be serialized as an ISO string, but the Z suffix behavior might differ
    # Check that it starts with the expected date/time part
    assert serialized["closed"].startswith("2023-01-01T12:00:00")


def test_question_with_object_one_of():
    # Test creating a Question with Object in one_of field
    nested_obj = Object(id="http://example.com/optionA", name="Option A")
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        one_of=nested_obj,
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    # The nested object should be loaded properly
    assert question.one_of is not None
    assert hasattr(question.one_of, "id")


def test_question_with_object_any_of():
    # Test creating a Question with Object in any_of field
    nested_obj = Object(id="http://example.com/optionB", name="Option B")
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        any_of=nested_obj,
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    # The nested object should be loaded properly
    assert question.any_of is not None
    assert hasattr(question.any_of, "id")


def test_question_with_object_closed():
    # Test creating a Question with Object in closed field
    nested_obj = Object(id="http://example.com/closed_reason", name="Closed Reason")
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        closed=nested_obj,
    )

    assert question.id == "http://example.com/question/1"
    assert question.name == "Test Question"
    # The nested object should be loaded properly
    assert question.closed is not None
    assert hasattr(question.closed, "id")


def test_question_serialization():
    # Test full serialization of a Question
    question = Question(
        id="http://example.com/question/1",
        name="Test Question",
        one_of="Option A",
        any_of="Option B",
        closed="2023-01-01T12:00:00Z",  # Use a string instead of False to ensure it appears in serialization
    )

    serialized = question.model_dump(by_alias=True)

    assert serialized["id"] == "http://example.com/question/1"
    assert serialized["name"] == "Test Question"
    assert serialized["oneOf"] == "Option A"
    assert serialized["anyOf"] == "Option B"
    assert serialized["closed"] == "2023-01-01T12:00:00Z"
    assert serialized["type"] == "Question"
