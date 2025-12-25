from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadArc(AcadEntity):
    def __init__(self, obj) -> None: ...
    ArcLength: float
    Area: float
    Center: PyGePoint3d
    EndAngle: float
    EndPoint: PyGePoint3d
    Normal: PyGeVector3d
    Radius: float
    StartAngle: float
    StartPoint: PyGePoint3d
    Thickness: float
    TotalAngle: float
    def Copy(self) -> AcadArc: ...
    def Offset(self, Distance: float) -> vObjectArray: ...
