from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface



class AcadExtrudedSurface(AcadSurface):
    def __init__(self, obj) -> None: super().__init__(obj)

    Direction: PyGeVector3d = proxy_property('PyGeVector3d','Direction',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    TaperAngle: float = proxy_property(float,'TaperAngle',AccessMode.ReadWrite)

    def Copy(self) -> AcadExtrudedSurface:
        return AcadExtrudedSurface(self._obj.Copy())