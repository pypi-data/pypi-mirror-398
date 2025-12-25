from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadHatch(AcadEntity):
    def __init__(self, obj) -> None: ...
    Area: float
    AssociativeHatch: bool
    BackgroundColor: AcadAcCmColor
    Elevation: float
    GradientAngle: float
    GradientCentered: bool
    GradientColor1: AcadAcCmColor
    GradientColor2: AcadAcCmColor
    GradientName: str
    HatchObjectType: AcHatchObjectType
    HatchStyle: AcHatchStyle
    ISOPenWidth: AcISOPenWidth
    Normal: PyGeVector3d
    NumberOfLoops: int
    Origin: PyGePoint3d
    PatternAngle: float
    PatternDouble: bool
    PatternName: str
    PatternScale: float
    PatternSpace: float
    PatternType: AcPatternType
    def AppendInnerLoop(self, Loop: vObjectArray[AcadArc | AcadCircle | AcadEllipse | AcadLine | AcadPolyline | AcadRegion | AcadSpline]) -> None: ...
    def AppendOuterLoop(self, Loop: vObjectArray[AcadArc | AcadCircle | AcadEllipse | AcadLine | AcadPolyline | AcadRegion | AcadSpline]) -> None: ...
