from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadLine(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Angle: float = proxy_property(float,'Angle',AccessMode.ReadOnly)
    Delta: vDoubleArray = proxy_property('vDoubleArray','Delta',AccessMode.ReadOnly)
    EndPoint: PyGePoint3d = proxy_property('PyGePoint3d','EndPoint',AccessMode.ReadWrite)
    Length: float = proxy_property(float,'Length',AccessMode.ReadOnly)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    StartPoint: PyGePoint3d = proxy_property('PyGePoint3d','StartPoint',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)

    def Offset(self, Distance: float) -> vObjectArray:
        return vObjectArray(self._obj.Offset(Distance))

    def Copy(self) -> AcadLine:
        return AcadLine(self._obj.Copy())