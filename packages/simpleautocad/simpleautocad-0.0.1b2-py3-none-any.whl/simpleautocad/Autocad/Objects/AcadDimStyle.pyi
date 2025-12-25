from ..Base import *
from ..Proxy import *
from ..AcadObject import AcadObject as AcadObject

class AcadDimStyle(AcadObject):
    def __init__(self, obj) -> None: ...
    Name: str
    def CopyFrom(self, SourceObject: AcadDimStyle | AcadDim3PointAngular | AcadDimAligned | AcadDimAngular | AcadDimArcLength | AcadDimDiametric | AcadDimOrdinate | AcadDimRadial | AcadDimRadialLarge | AcadDimRotated | AcadDocument | AcadLayout | AcadLeader | AcadPlotConfiguration) -> None: ...
