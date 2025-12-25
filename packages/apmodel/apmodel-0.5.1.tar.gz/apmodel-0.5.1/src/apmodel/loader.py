import warnings
from typing import Any, Optional

from pyld import jsonld
from typing_extensions import Literal

from apmodel.context import LDContext

from ._core._jsonjd.loader import create_document_loader
from .registry import registry
from .types import ActivityPubModel


def load(
    data: Any,
    default: Literal["raw"] | Optional[ActivityPubModel] = None,
    parent_context: Optional[LDContext] = None,
) -> Optional[dict | str | list | ActivityPubModel]:
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        return [load(item, default, parent_context) for item in data]

    if not isinstance(data, dict):
        return data

    data_to_validate = data.copy()

    if "@context" not in data_to_validate and parent_context:
        data_to_validate["@context"] = parent_context  # .model_dump()

    current_context = data_to_validate.get("@context")

    jsonld_options = {"documentLoader": create_document_loader()}

    data_expanded = data_to_validate
    if current_context:
        try:
            expanded = jsonld.expand(data_to_validate, options=jsonld_options)
            if isinstance(expanded, list) and expanded:
                data_expanded = expanded[0]
            elif isinstance(expanded, dict):
                data_expanded = expanded
        except Exception:
            pass

    expanded_type = None
    if isinstance(data_expanded, dict):
        expanded_type = data_expanded.get("@type")
        if isinstance(expanded_type, list) and expanded_type:
            expanded_type = expanded_type[0]

    if isinstance(expanded_type, str):
        if model_cls := registry.get(expanded_type):
            try:
                model_creation_context = {"ld_context": current_context}
                model = model_cls.model_validate(
                    data_to_validate, context=model_creation_context
                )
                return model
            except Exception as e:
                warnings.warn(
                    f"WARNING: Validation failed for type {expanded_type} "
                    f"with data {data_to_validate}: {e}"
                )

    if default == "raw":
        return data
    return default
