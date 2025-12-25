---
icon: lucide/rocket
---

# Migrating from 0.4.x to 0.5.x

apmodel 0.5.x introduces a significant rewrite of the library's core, migrating from Python's `dataclasses` to `Pydantic`. This change enhances type validation, serialization, and overall robustness. However, it introduces several breaking changes.

## Key Changes

1.  **Migration to Pydantic**: All models now inherit from `pydantic.BaseModel` instead of being `dataclasses`. This provides automatic type validation and more powerful data handling.
2.  **Serialization Method**: The `dump()` function and `.to_json()` methods have been removed. Use the new `apmodel.to_dict()` function for serializing models to JSON-LD dictionaries.
3.  **`_extra` Field Renamed**: The field for storing unknown properties has been renamed from `_extra` to `model_extra`. You can access it via `model.model_extra`.
4.  **`Undefined` Class Removed**: The `Undefined` class has been removed. Optional fields that are not present will now be `None`.
5.  **`LDContext.json` Property Removed**: The `.json` property on `LDContext` instances is removed. Use the `.definitions` property to access the context dictionary directly.
6.  **Key Management**: Key handling in `CryptographicKey` and `Multikey` has been improved. Key fields are now automatically serialized and deserialized from/to their respective string/object formats.

## Migration Guide

### 1. Model Serialization

The global `dump()` function and the `.to_json()` method on models are no longer available. Use the new `apmodel.to_dict()` function.

**Before (v0.4.x):**

```python
import apmodel
from apmodel.vocab import Note

note = Note(content="Hello")
json_dict = note.to_json()
# or
json_string = apmodel.dump(note)
```

**After (v0.5.x):**

```python
import apmodel
from apmodel.vocab import Note

note = Note(content="Hello")
json_dict = apmodel.to_dict(note)
```

### 2. Accessing Extra/Unknown Properties

If you relied on accessing properties not defined in the model, you need to update the field name from `_extra` to `model_extra`.

**Before (v0.4.x):**

```python
data = {"type": "Note", "content": "A note", "myCustomField": 123}
note = apmodel.load(data)
custom_value = note._extra["myCustomField"]
```

**After (v0.5.x):**

```python
data = {"type": "Note", "content": "A note", "myCustomField": 123}
note = apmodel.load(data)
# Pydantic's `extra` is accessed via `model_extra`
custom_value = note.model_extra["myCustomField"]
```

### 3. Checking for Optional Fields

Fields that were previously `Undefined` will now be `None` if they are not provided. Update your checks accordingly.

**Before (v0.4.x):**

```python
from apmodel.types import Undefined

if note.summary is not Undefined:
    # ...
```

**After (v0.5.x):**

```python
if note.summary is not None:
    # ...
```

### 4. `LDContext` Usage

The `.json` property for accessing the dictionary part of a context is removed. Use `.definitions`.

**Before (v0.4.x):**
```python
from apmodel import LDContext

ctx = LDContext([{"myTerm": "http://example.com/term"}])
defs = ctx.json  # -> {"myTerm": "http://example.com/term"}
```

**After (v0.5.x):**
```python
from apmodel.context import LDContext

ctx = LDContext([{"myTerm": "http://example.com/term"}])
defs = ctx.definitions  # -> {"myTerm": "http://example.com/term"}
```

### 5. Renaming variables
In apmodel 0.5.x, the names of values used to access models have been changed from camel case to snake case. However, they are automatically converted back to camel case during loading and output.

**Before (v0.4.x):**
```python
actor = apmodel.load(data)
public_key = actor.publicKey
```

**Before (v0.5.x):**
```python
actor = apmodel.load(data)
public_key = actor.public_key
```

## 6. Access keys
Key access via `CryptographicKey` and `Multikey` has been improved.

Instead of accessing via the traditional publicKeyPem or publicKeyMultibase, you can access the public key by accessing the public_key of each model, allowing you to access the loaded public key as before.

**Before (v0.4.x):**
```python
actor = apmodel.load(data)
crypto_key = actor.publicKey
public_key = crypto_key.publicKeyPem
```

**Before (v0.5.x):**
```python
actor = apmodel.load(data)
crypto_key = actor.public_key
public_key = crypto_key.public_key
```