---
icon: lucide/code
---

# Usage

`apmodel` is designed to be intuitive for loading and serializing ActivityPub objects. Here are the basic usage patterns.

## Loading JSON into Models

The primary function for parsing data is `apmodel.load()`. It takes a dictionary and automatically determines the correct model class based on the `type` field.

```python
import apmodel
import json

json_data = """
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "id": "http://example.org/notes/1",
  "content": "This is a simple note",
  "published": "2025-12-19T10:00:00Z"
}
"""

data = json.loads(json_data)
note = apmodel.load(data)

print(type(note))
# Expected output: <class 'apmodel.vocab.note.Note'>

print(note.id)
# Expected output: http://example.org/notes/1

print(note.content)
# Expected output: This is a simple note
```

If a matching model for the `type` is not found, `load()` will return the original dictionary by default.

## Serializing Models to Dictionaries

To convert a model instance back into a dictionary, use the `apmodel.to_dict()` function. This function intelligently aggregates JSON-LD contexts from nested models.

```python
import apmodel
from apmodel.vocab import Person
from apmodel.extra.security import CryptographicKey

# Create a Person model
person = Person(
    id="https://example.com/users/alice",
    name="Alice",
    preferred_username="alice",
    public_key=CryptographicKey(
        id="https://example.com/users/alice#main-key",
        owner="https://example.com/users/alice",
        public_key_pem="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
    )
)

# Convert the model to a dictionary
person_dict = apmodel.to_dict(person)

print(person_dict["type"])
# Expected output: Person

print(person_dict["preferredUsername"])
# Expected output: alice

# The context from CryptographicKey is automatically merged
print("@context" in person_dict)
# Expected output: True
# The resulting context will contain both ActivityStreams and Security vocabularies.
```

The resulting dictionary is ready to be serialized to a JSON string with `json.dumps()`.
