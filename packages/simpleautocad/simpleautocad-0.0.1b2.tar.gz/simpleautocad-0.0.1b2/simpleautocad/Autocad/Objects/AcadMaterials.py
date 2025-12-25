from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadMaterial import AcadMaterial


class AcadMaterials(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str) -> AcadMaterial: 
        return AcadMaterial(self._obj.Add(Name))

    def Item(self, Index: int) -> AcadMaterial: 
        return AcadMaterial(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadMaterial(item)
            yield obj