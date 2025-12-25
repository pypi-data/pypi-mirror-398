---
icon: lucide/rocket
---

# apmodel

**A Python implementation of ActivityStreams 2.0 models and other Fediverse-related vocabularies.**

`apmodel` provides robust, Pydantic-based models for building applications that interact with the Fediverse. It simplifies handling JSON-LD by automatically parsing it into Python objects and serializing them back.

## Features

-   **Pydantic-based Models**: Strong typing, validation, and easy configuration.
-   **Automatic JSON-LD Handling**: Seamlessly load data into models and serialize models back to JSON-LD aware dictionaries.
-   **Extensive Vocabulary Support**:
    -   ActivityStreams 2.0 Core Types
    -   Activity Vocabulary (Create, Like, Announce, etc.)
    -   Actor Types (Person, Application, Service, etc.)
    -   Object Types (Note, Article, etc.)
    -   W3C Security Vocabulary (CryptographicKey, DataIntegrityProof, Multikey)
    -   NodeInfo 2.0/2.1
-   **Intelligent Context Management**: Automatically aggregates and builds the correct `@context` for serialized objects.

## Quick Start

Here's a quick example of how to load and serialize an ActivityStreams `Note`.

```python
import apmodel
import json

# A simple Note object in JSON
note_json = """
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "id": "http://example.com/notes/1",
  "content": "This is a simple note!"
}
"""

# 1. Load the JSON into an apmodel object
note_obj = apmodel.load(json.loads(note_json))

print(f"Loaded object of type: {type(note_obj)}")
print(f"Content: {note_obj.content}")

# 2. Serialize the object back to a dictionary
note_dict = apmodel.to_dict(note_obj)

print("Serialized dictionary:")
print(json.dumps(note_dict, indent=2))
```

Dive into the **[Usage](./usage.md)** and **[API Reference](./api/index.md)** sections to learn more.
