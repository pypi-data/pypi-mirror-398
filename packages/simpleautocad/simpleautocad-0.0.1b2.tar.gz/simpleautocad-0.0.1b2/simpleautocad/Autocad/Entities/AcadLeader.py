from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadLeader(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Annotation: AcadBlockReference | AcadMtext | AcadTolerance  = proxy_property('AppObject','Annotation',AccessMode.ReadWrite)
    ArrowheadBlock: str = proxy_property(str,'ArrowheadBlock',AccessMode.ReadWrite)
    ArrowheadSize: float = proxy_property(float,'ArrowheadSize',AccessMode.ReadWrite)
    ArrowheadType: AcDimArrowheadType = proxy_property(float,'ArrowheadType',AccessMode.ReadWrite)
    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    DimensionLineColor: AcColor = proxy_property('AcColor','DimensionLineColor',AccessMode.ReadWrite)
    DimensionLineWeight: AcLineWeight = proxy_property('AcLineWeight','DimensionLineWeight',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    TextGap: float = proxy_property(float,'TextGap',AccessMode.ReadWrite)
    Type: AcLeaderType = proxy_property('AcLeaderType','Type',AccessMode.ReadWrite)


    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))
    
    def Copy(self) -> AcadLeader:
        return AcadLeader(self._obj.Copy())
    
    def Evaluate(self) -> None:
        self._obj.Evaluate()
