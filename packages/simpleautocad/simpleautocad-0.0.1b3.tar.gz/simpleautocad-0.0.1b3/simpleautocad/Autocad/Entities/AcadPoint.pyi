from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadPoint(AcadEntity):
    def __init__(self, obj) -> None: ...
    Coordinates: PyGePoint3d
    Normal: PyGeVector3d
    Thickness: float
    def Copy(self) -> AcadPoint: ...
