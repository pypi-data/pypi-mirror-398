from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import IAcadObjectCollection
from .AcadDimStyle import AcadDimStyle



class AcadDimStyles(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str) -> AcadDimStyle: 
        return AcadDimStyle(self._obj.Add(Name))

    def Item(self, Index: int) -> AcadDimStyle:
        return AcadDimStyle(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadDimStyle(item)
            yield obj
