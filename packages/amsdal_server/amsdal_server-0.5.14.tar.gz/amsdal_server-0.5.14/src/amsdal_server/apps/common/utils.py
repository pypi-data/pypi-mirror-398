from amsdal_models.classes.class_manager import ClassManager
from amsdal_models.classes.model import Model
from amsdal_models.classes.model import TypeModel
from amsdal_models.classes.utils import is_partial_model
from amsdal_utils.models.base import ModelBase
from amsdal_utils.models.enums import ModuleType


def build_missing_models() -> list[str]:
    return []


async def async_build_missing_models() -> list[str]:
    return []


def get_subclasses(class_item: type[ModelBase] | None) -> list[type[ModelBase]]:
    builtin_models = []
    found_classes = []

    if class_item is not None:
        if class_item in (ModelBase, TypeModel, Model):
            return []

        for subclass in class_item.__subclasses__():
            if class_item in (ModelBase, TypeModel, Model) or is_partial_model(subclass):
                continue

            if subclass.__module__ == 'builtins':
                builtin_models.append(subclass)
                continue

            found_classes.append(subclass)
            found_classes.extend(get_subclasses(subclass))

    if builtin_models:
        _fund_model_names = [_model.__name__ for _model in found_classes]

        for builtin_model in builtin_models:
            if is_partial_model(builtin_model):
                continue

            if builtin_model.__name__ not in _fund_model_names:
                found_classes.append(builtin_model)
                found_classes.extend(get_subclasses(builtin_model))

    return found_classes


def import_class_model(class_name: str) -> type[Model]:
    class_manager = ClassManager()

    return class_manager.import_class(class_name, ModuleType.USER)
