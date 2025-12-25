from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadEllipse(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    Center: PyGePoint3d = proxy_property('PyGePoint3d','Center',AccessMode.ReadWrite)
    EndAngle: float = proxy_property(float,'EndAngle',AccessMode.ReadWrite)
    EndParameter: float = proxy_property(float,'EndParameter',AccessMode.ReadWrite)
    EndPoint: PyGePoint3d = proxy_property('PyGePoint3d','EndPoint',AccessMode.ReadWrite)
    MajorAxis: PyGeVector3d = proxy_property('PyGeVector3d','MajorAxis',AccessMode.ReadWrite)
    MajorRadius: float = proxy_property(float,'MajorRadius',AccessMode.ReadWrite)
    MinorAxis: PyGeVector3d = proxy_property('PyGeVector3d','MajorAxis',AccessMode.ReadOnly)
    MinorRadius: float = proxy_property(float,'MinorRadius',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    RadiusRatio: float = proxy_property(float,'RadiusRatio',AccessMode.ReadWrite)
    StartAngle: float = proxy_property(float,'StartAngle',AccessMode.ReadWrite)
    StartParameter: float = proxy_property(float,'StartParameter',AccessMode.ReadWrite)
    StartPoint: PyGePoint3d = proxy_property('PyGePoint3d','StartPoint',AccessMode.ReadWrite)

    def Copy(self) -> AcadEllipse:
        return AcadEllipse(self._obj.Copy())

    def Offset(self, Distance: float) -> AcadEllipse:
        return AcadEllipse(self._obj.Offset(Distance))
