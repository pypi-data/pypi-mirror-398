from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadArc(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    ArcLength: float = proxy_property(float,'ArcLength',AccessMode.ReadOnly)
    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    Center: PyGePoint3d = proxy_property('PyGePoint3d','Center',AccessMode.ReadWrite)
    EndAngle: float = proxy_property(float,'EndAngle',AccessMode.ReadWrite)
    EndPoint: PyGePoint3d = proxy_property('PyGePoint3d','EndPoint',AccessMode.ReadOnly)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Radius: float = proxy_property(float,'Radius',AccessMode.ReadWrite)
    StartAngle: float = proxy_property(float,'StartAngle',AccessMode.ReadWrite)
    StartPoint: PyGePoint3d = proxy_property('PyGePoint3d','StartPoint',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)
    TotalAngle: float = proxy_property(float,'TotalAngle',AccessMode.ReadOnly)

    def Copy(self) -> AcadArc:
        return AcadArc(self._obj.Copy())

    def Offset(self, Distance: float) -> vObjectArray:
        return vObjectArray(self._obj.Offset(Distance))