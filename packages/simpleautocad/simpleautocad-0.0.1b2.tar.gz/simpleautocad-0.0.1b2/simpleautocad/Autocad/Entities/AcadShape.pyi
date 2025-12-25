from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadShape(AcadEntity):
    def __init__(self, obj) -> None: ...
    InsertionPoint: PyGePoint3d
    Name: str
    Normal: PyGeVector3d
    ObliqueAngle: float
    Rotation: float
    ScaleFactor: float
    Thickness: float
    def Copy(self) -> AcadShape: ...
