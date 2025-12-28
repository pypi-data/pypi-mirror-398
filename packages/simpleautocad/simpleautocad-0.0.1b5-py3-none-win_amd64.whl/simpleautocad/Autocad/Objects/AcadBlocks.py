from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import IAcadObjectCollection
from .AcadBlock import AcadBlock


class AcadBlocks(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, InsertionPoint: PyGePoint3d, Name: str) -> AcadBlock:
        return AcadBlock(self._obj.Add(InsertionPoint(), Name))

    def Item(self, Index: int) -> AcadBlock:
        return AcadBlock(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            yield AcadBlock(item)