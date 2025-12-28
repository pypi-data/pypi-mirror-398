from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlock import IAcadBlock


class AcadPaperSpace(IAcadBlock):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)

    def AddPViewport(self, Center: PyGePoint3d, Width: float, Height: float) -> AcadPViewport:
        return AcadPViewport(self._obj.AddPViewport(Center(), Width, Height))

