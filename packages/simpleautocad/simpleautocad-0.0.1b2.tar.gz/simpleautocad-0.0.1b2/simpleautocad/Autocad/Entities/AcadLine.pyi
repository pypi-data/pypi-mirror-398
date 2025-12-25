from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadLine(AcadEntity):
    def __init__(self, obj) -> None: ...
    Angle: float
    Delta: vDoubleArray
    EndPoint: PyGePoint3d
    Length: float
    Normal: PyGeVector3d
    StartPoint: PyGePoint3d
    Thickness: float
    def Offset(self, Distance: float) -> vObjectArray: ...
    def Copy(self) -> AcadLine: ...
