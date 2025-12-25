from __future__ import annotations
from ..Base import *
from ..Proxy import *
# from ..AcadObject import *
from .AcadToolbar import *

class AcadToolbars(AppObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    LargeButtons: bool = proxy_property(bool,'LargeButtons',AccessMode.ReadWrite)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)

    def Add(self, Name: str) -> AcadToolbar:
        return AcadToolbar(self._obj.Add(Name))

    def Item(self, Index: int | str) -> AcadToolbar:
        return AcadToolbar(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadToolbar(item)
            yield obj
