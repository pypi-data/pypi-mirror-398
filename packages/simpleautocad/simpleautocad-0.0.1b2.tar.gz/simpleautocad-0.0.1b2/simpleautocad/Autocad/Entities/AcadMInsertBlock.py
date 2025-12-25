from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadBlockReference import AcadBlockReference



class AcadMInsertBlock(AcadBlockReference):
    def __init__(self, obj) -> None: super().__init__(obj)

    Columns: int = proxy_property(int,'Columns',AccessMode.ReadWrite)
    ColumnSpacing: float = proxy_property(float,'ColumnSpacing',AccessMode.ReadWrite)

    def Copy(self) -> AcadMInsertBlock:
        return AcadMInsertBlock(self._obj.Copy())