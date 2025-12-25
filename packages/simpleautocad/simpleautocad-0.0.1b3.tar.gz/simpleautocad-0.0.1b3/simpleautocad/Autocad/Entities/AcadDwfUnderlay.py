from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadUnderlay import AcadUnderlay



class AcadDwfUnderlay(AcadUnderlay):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Copy(self) -> AcadDwfUnderlay:
        return AcadDwfUnderlay(self._obj.Copy())
