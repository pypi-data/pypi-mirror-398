from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadSection(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    BottomHeight: int = proxy_property(int,'BottomHeight',AccessMode.ReadWrite)
    Elevation: float = proxy_property(float,'Elevation',AccessMode.ReadWrite)
    IndicatorFillColor: AcadAcCmColor = proxy_property('AcadAcCmColor','IndicatorFillColor',AccessMode.ReadWrite)
    IndicatorTransparency: int = proxy_property(int,'IndicatorTransparency',AccessMode.ReadWrite)
    LiveSectionEnabled: bool = proxy_property(bool,'LiveSectionEnabled',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    NumVertices: int = proxy_property(int,'NumVertices',AccessMode.ReadWrite)
    SectionPlaneOffset: float = proxy_property(float,'SectionPlaneOffset',AccessMode.ReadWrite)
    Settings: AcadSectionSettings = proxy_property('AcadSectionSettings','Settings',AccessMode.ReadOnly)
    SliceDepth: float = proxy_property(float,'SliceDepth',AccessMode.ReadWrite)
    State: AcSectionState = proxy_property('AcSectionState','State',AccessMode.ReadWrite)
    State2: AcSectionState2 = proxy_property('AcSectionState2','State2',AccessMode.ReadWrite)
    TopHeight: float = proxy_property(float,'TopHeight',AccessMode.ReadWrite)
    VerticalDirection: PyGeVector3d = proxy_property('PyGeVector3d','VerticalDirection',AccessMode.ReadWrite)
    Vertices: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Vertices',AccessMode.ReadWrite)
    ViewingDirection: PyGeVector3d = proxy_property('PyGeVector3d','ViewingDirection',AccessMode.ReadWrite)

    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))
    
    def AddVertex(self, Index: int, Point: PyGePoint3d) -> None:
        self._obj.AddVertex(Index, Point())
    
    def Copy(self) -> AcadSection:
        return AcadSection(self._obj.Copy())
        
    def CreateJog(self, varPt: PyGePoint3d) -> None:
        self._obj.CreateJog(varPt())
        
    def GenerateSectionGeometry(self, pEntity: AcadEntity) -> tuple[vObjectArray]:
        pIntersectionBoundaryObjs, pIntersectionFillObjs, pBackgroudnObjs, pForegroudObjs, pCurveTangencyObjs = self._obj.GenerateSectionGeometry(pEntity)
        return vObjectArray(pIntersectionBoundaryObjs), \
                vObjectArray(pIntersectionFillObjs), \
                vObjectArray(pBackgroudnObjs), \
                vObjectArray(pForegroudObjs), \
                vObjectArray(pCurveTangencyObjs)

    def HitTest(self, varPtHit: PyGePoint3d) -> tuple[bool,int,Variant,AcSectionSubItem]:
        pHit, pSegmentIndex, pPtOnSegment, pSubItem = self._obj.HitTest(varPtHit())
        return bool(pHit), int(pSegmentIndex), Variant(pPtOnSegment), AcSectionSubItem(pSubItem)

    def RemoveVertex(self, nIndex: int) -> None:
        self._obj.RemoveVertex(nIndex)
