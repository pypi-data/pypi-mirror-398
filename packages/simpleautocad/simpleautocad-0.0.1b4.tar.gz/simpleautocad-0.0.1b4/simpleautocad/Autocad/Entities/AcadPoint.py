from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPoint(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3d = proxy_property('PyGePoint3d','Coordinates',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)

    def Copy(self) -> AcadPoint:
        return AcadPoint(self._obj.Copy())