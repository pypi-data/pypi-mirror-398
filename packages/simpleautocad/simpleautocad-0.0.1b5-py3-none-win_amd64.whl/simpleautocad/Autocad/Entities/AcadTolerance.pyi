from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadTolerance(AcadEntity):
    def __init__(self, obj) -> None: ...
    DimensionLineColor: AcColor
    DirectionVector: PyGeVector3d
    InsertionPoint: PyGePoint3d
    Normal: PyGeVector3d
    ScaleFactor: float
    StyleName: str
    TextColor: AcColor
    TextHeight: float
    TextString: str
    TextStyle: AcadTextStyle
