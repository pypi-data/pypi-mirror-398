from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadCircle(AcadEntity):
    def __init__(self, obj) -> None: ...
    Area: float
    Center: PyGePoint3d
    Circumference: float
    Diameter: float
    Normal: PyGeVector3d
    Radius: float
    Thickness: float
    def Copy(self) -> AcadCircle: ...
    def Offset(self, Distance: float) -> vObjectArray: ...
