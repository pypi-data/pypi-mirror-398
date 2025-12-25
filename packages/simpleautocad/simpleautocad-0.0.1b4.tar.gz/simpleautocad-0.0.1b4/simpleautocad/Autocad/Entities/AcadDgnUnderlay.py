from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadUnderlay import AcadUnderlay



class AcadDgnUnderlay(AcadUnderlay):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Copy(self) -> AcadDgnUnderlay:
        return AcadDgnUnderlay(self._obj.Copy())
