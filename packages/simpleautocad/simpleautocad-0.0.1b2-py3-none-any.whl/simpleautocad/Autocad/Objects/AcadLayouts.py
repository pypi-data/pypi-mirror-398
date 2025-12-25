from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadLayout import *



class AcadLayouts(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, InsertionPoint: PyGePoint3d, Name: str) -> AcadLayout:
        return AcadLayout(self._obj.Add(InsertionPoint(), Name))

    def Item(self, Index: int) -> AcadLayout:
        return AcadLayout(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadLayout(item)
            yield obj
