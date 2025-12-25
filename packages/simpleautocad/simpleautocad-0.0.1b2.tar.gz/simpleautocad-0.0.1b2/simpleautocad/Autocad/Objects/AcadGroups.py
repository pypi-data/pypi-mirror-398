from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadGroups(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str) -> AcadGroup: 
        return AcadGroup(self._obj.Add(Name))

    def Item(self, Index: int | str) -> AcadGroup:
        return AcadGroup(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadGroup(item)
            yield obj