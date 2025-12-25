from typing import TypeVar, Type
from pydantic import TypeAdapter

T = TypeVar("T")


class Setting:
    settings_model: TypeAdapter[T]
    settings_doc: str
    scoped: bool

    def __init__(self, settings_model: Type[T], settings_doc: str = "", scoped: bool = False):
        self.settings_doc = settings_doc or settings_model.__doc__
        self.settings_model = TypeAdapter(settings_model)
        self.scoped = scoped
