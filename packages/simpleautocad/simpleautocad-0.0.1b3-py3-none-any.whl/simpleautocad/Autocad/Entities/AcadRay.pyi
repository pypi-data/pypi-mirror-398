from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadRay(AcadEntity):
    def __init__(self, obj) -> None: ...
    BasePoint: PyGePoint3d
    DirectionVector: PyGeVector3d
    SecondPoint: PyGePoint3d
    def Copy(self) -> AcadRay: ...
