from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadLeader(AcadEntity):
    def __init__(self, obj) -> None: ...
    Annotation: AcadBlockReference | AcadMtext | AcadTolerance
    ArrowheadBlock: str
    ArrowheadSize: float
    ArrowheadType: AcDimArrowheadType
    Coordinates: PyGePoint3dArray
    DimensionLineColor: AcColor
    DimensionLineWeight: AcLineWeight
    Normal: PyGeVector3d
    TextGap: float
    Type: AcLeaderType
    def Coordinate(self, Index: int) -> PyGePoint3d: ...
    def Copy(self) -> AcadLeader: ...
    def Evaluate(self) -> None: ...
