from __future__ import annotations
from ..Proxy import *
from ..AcadObject import IAcadObjectCollection
from .AcadDictionary import AcadDictionary

class AcadDictionaries(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str = None) -> AcadDictionary:
        return AcadDictionary(self._obj.Add(Name))

    # def Item(self, Index: int) -> AcadDictionary:
    #     return AcadDictionary(self._obj.Item(Index))

    # def __iter__(self):
    #     for item in self._obj:
    #         obj = AcadDictionary(item)
    #         yield obj
