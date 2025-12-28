from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadUnderlay import AcadUnderlay



class AcadPdfUnderlay(AcadUnderlay):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Copy(self) -> AcadPdfUnderlay: 
        return AcadPdfUnderlay(self._obj.Copy())
