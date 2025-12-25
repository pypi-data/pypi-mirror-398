from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadExternalReference import AcadExternalReference



class AcadComparedReference(AcadExternalReference):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Copy(self) -> AcadComparedReference:
        return AcadComparedReference(self._obj.Copy())
