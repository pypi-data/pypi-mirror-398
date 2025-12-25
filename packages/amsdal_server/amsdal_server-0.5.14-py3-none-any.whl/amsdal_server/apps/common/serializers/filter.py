from enum import Enum
from enum import auto
from typing import Annotated
from typing import Any
from urllib.parse import unquote

from pydantic import AfterValidator
from pydantic import BaseModel


# TODO: Extend to support IN, case-sensitive
class FilterType(Enum):
    eq = auto()
    neq = auto()
    gt = auto()
    gte = auto()
    lt = auto()
    lte = auto()
    contains = auto()
    icontains = auto()
    startswith = auto()
    istartswith = auto()
    endswith = auto()
    iendswith = auto()


def _unquote_target(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return unquote(value)
        except Exception:
            return value
    return value


class Filter(BaseModel):
    key: str
    filter_type: FilterType
    target: Annotated[Any, AfterValidator(_unquote_target)]

    def __str__(self) -> str:
        return f"Filter('{self.key}' {self.filter_type.name} '{self.target}')"

    def __repr__(self) -> str:
        return str(self)
