from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadRay(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    BasePoint: PyGePoint3d = proxy_property('PyGePoint3d','BasePoint',AccessMode.ReadWrite)
    DirectionVector: PyGeVector3d = proxy_property('PyGeVector3d','DirectionVector',AccessMode.ReadWrite)
    SecondPoint: PyGePoint3d = proxy_property('PyGePoint3d','SecondPoint',AccessMode.ReadWrite)

    def Copy(self) -> AcadRay:
        return AcadRay(self._obj.Copy())