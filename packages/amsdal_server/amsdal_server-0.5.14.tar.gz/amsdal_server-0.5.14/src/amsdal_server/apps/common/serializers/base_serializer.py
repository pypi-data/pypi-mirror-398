from typing import Any

from pydantic import BaseModel


class SkipNoneBaseModel(BaseModel):
    def _preprocess_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        kwargs['exclude_none'] = True

        return kwargs

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        return super().model_dump(**self._preprocess_kwargs(kwargs))

    def model_dump_json(self, **kwargs: Any) -> str:
        return super().model_dump_json(**self._preprocess_kwargs(kwargs))
