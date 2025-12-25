import importlib
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

from apmodel._core._initial._registry_bootstrap import TYPE_MAPPING

if TYPE_CHECKING:
    from .types import ActivityPubModel


BASE_MODEL_NAMES = {
    "Object",
    "Link",
    "Activity",
    "IntransitiveActivity",
    "Collection",
    "OrderedCollection",
    "CollectionPage",
    "OrderedCollectionPage",
}


def _load_model_cls(path: str) -> Type["ActivityPubModel"]:
    """
    example: "apmodel.extra.emoji.Emoji"
    """
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class ModelRegistry:
    def __init__(
        self, preload_mapping: Dict[str, str | Type["ActivityPubModel"]]
    ) -> None:
        self._registry: Dict[str, Union[str, Type["ActivityPubModel"]]] = {
            **preload_mapping
        }

    def register(
        self,
        model_cls: Union[str, Type["ActivityPubModel"]],
        model_type: str,
    ):
        import warnings

        if model_type in self._registry:
            existing_cls_or_path = self._registry[model_type]
            if isinstance(existing_cls_or_path, str):
                existing_cls = self.get(model_type)
            else:
                existing_cls = existing_cls_or_path

            if isinstance(model_cls, str):
                model_cls_obj = _load_model_cls(model_cls)
            else:
                model_cls_obj = model_cls

            if (
                existing_cls
                and issubclass(model_cls_obj, existing_cls)
                and existing_cls.__name__ not in BASE_MODEL_NAMES
            ):
                self._registry[model_type] = model_cls_obj
            else:
                warnings.warn(
                    f"Model type '{model_type}' for class {model_cls_obj.__name__} conflicts with "
                    f"existing model {existing_cls.__name__ if existing_cls else 'None'}. Registration skipped due to "
                    f"missing inheritance relationship or attempting to override a base model.",
                    UserWarning,
                    stacklevel=2,
                )
        else:
            self._registry[model_type] = model_cls

    def get(self, model_type: str) -> Optional[Type["ActivityPubModel"]]:
        cls_or_path = self._registry.get(model_type)
        if isinstance(cls_or_path, str):
            cls = _load_model_cls(cls_or_path)
            self._registry[model_type] = cls  # cache
            return cls
        return cls_or_path

    def all(self) -> Dict[str, Type["ActivityPubModel"]]:
        loaded_registry: Dict[str, Type["ActivityPubModel"]] = {}
        for model_type, cls_or_path in self._registry.items():
            if isinstance(cls_or_path, str):
                cls = _load_model_cls(cls_or_path)
                self._registry[model_type] = cls
                loaded_registry[model_type] = cls
            else:
                loaded_registry[model_type] = cls_or_path
        return loaded_registry

    def has(self, model_type: str) -> bool:
        return model_type in self._registry


registry = ModelRegistry(preload_mapping=TYPE_MAPPING)
