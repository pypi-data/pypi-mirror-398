from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadSection(AcadEntity):
    def __init__(self, obj) -> None: ...
    BottomHeight: int
    Elevation: float
    IndicatorFillColor: AcadAcCmColor
    IndicatorTransparency: int
    LiveSectionEnabled: bool
    Name: str
    Normal: PyGeVector3d
    NumVertices: int
    SectionPlaneOffset: float
    Settings: AcadSectionSettings
    SliceDepth: float
    State: AcSectionState
    State2: AcSectionState2
    TopHeight: float
    VerticalDirection: PyGeVector3d
    Vertices: PyGePoint3dArray
    ViewingDirection: PyGeVector3d
    def Coordinate(self, Index: int) -> PyGePoint3d: ...
    def AddVertex(self, Index: int, Point: PyGePoint3d) -> None: ...
    def Copy(self) -> AcadSection: ...
    def CreateJog(self, varPt: PyGePoint3d) -> None: ...
    def GenerateSectionGeometry(self, pEntity: AcadEntity) -> tuple[vObjectArray]: ...
    def HitTest(self, varPtHit: PyGePoint3d) -> tuple[bool, int, Variant, AcSectionSubItem]: ...
    def RemoveVertex(self, nIndex: int) -> None: ...
