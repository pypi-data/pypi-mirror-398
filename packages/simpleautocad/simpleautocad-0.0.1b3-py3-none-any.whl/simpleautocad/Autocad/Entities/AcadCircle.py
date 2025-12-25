from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadCircle(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadWrite)
    Center: PyGePoint3d = proxy_property('PyGePoint3d','Center',AccessMode.ReadWrite)
    Circumference: float = proxy_property(float,'Circumference',AccessMode.ReadWrite)
    Diameter: float = proxy_property(float,'Diameter',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Radius: float = proxy_property(float,'Radius',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)

    def Copy(self) -> AcadCircle:
        return AcadCircle(self._obj.Copy())

    def Offset(self, Distance: float) -> vObjectArray:
        return vObjectArray(self._obj.Offset(Distance))