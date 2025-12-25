from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadEllipse(AcadEntity):
    def __init__(self, obj) -> None: ...
    Area: float
    Center: PyGePoint3d
    EndAngle: float
    EndParameter: float
    EndPoint: PyGePoint3d
    MajorAxis: PyGeVector3d
    MajorRadius: float
    MinorAxis: PyGeVector3d
    MinorRadius: float
    Normal: PyGeVector3d
    RadiusRatio: float
    StartAngle: float
    StartParameter: float
    StartPoint: PyGePoint3d
    def Copy(self) -> AcadEllipse: ...
    def Offset(self, Distance: float) -> AcadEllipse: ...
