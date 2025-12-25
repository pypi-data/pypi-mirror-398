from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadView(AcadObject):
    def __init__(self, obj) -> None: ...
    CategoryName: str
    Center: PyGePoint2d
    Direction: PyGeVector3d
    HasVpAssociation: bool
    Height: float
    LayerState: str
    LayoutID: int
    Name: str
    Target: PyGePoint3d
    Width: float
