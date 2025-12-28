from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadSolid(AcadEntity):
    def __init__(self, obj) -> None: ...
    Coordinates: PyGePoint3dArray
    Normal: PyGeVector3d
    Thickness: float
    def Coordinate(self, Index: int) -> PyGePoint3d: ...
    def Copy(self) -> AcadSolid: ...
