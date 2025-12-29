from typing import Any
from typing import ClassVar

from amsdal_models.classes.model import TypeModel
from amsdal_utils.models.enums import ModuleType


class FrontendConfigSkipNoneBase(TypeModel):
    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs['exclude_none'] = True
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs: Any) -> str:
        kwargs['exclude_none'] = True
        return super().model_dump_json(**kwargs)
