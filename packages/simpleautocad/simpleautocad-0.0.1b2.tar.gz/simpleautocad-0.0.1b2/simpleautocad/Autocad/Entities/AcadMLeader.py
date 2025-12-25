from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity
from .AcadLeader import AcadLeader


class AcadMLeader(AcadEntity):
    def __init__(self, obj, leaderLineIndex=0) -> None: 
        self.leaderLineIndex = leaderLineIndex
        super().__init__(obj)

    ArrowheadBlock: str = proxy_property(str,'ArrowheadBlock',AccessMode.ReadWrite)
    ArrowheadSize: float = proxy_property(float,'ArrowheadSize',AccessMode.ReadWrite)
    ArrowheadType: AcDimArrowheadType = proxy_property(float,'ArrowheadType',AccessMode.ReadWrite)
    BlockConnectionType: AcBlockConnectionType = proxy_property('AcBlockConnectionType','BlockConnectionType',AccessMode.ReadWrite)
    BlockScale: int = proxy_property(int,'BlockScale',AccessMode.ReadWrite)
    ContentBlockName: str = proxy_property(str,'ContentBlockName',AccessMode.ReadWrite)
    ContentBlockType: AcPredefBlockType = proxy_property('AcPredefBlockType','ContentBlockType',AccessMode.ReadWrite)
    ContentType: AcMLeaderContentType = proxy_property('AcMLeaderContentType','ContentType',AccessMode.ReadWrite)
    DogLegged: bool = proxy_property(bool,'DogLegged',AccessMode.ReadWrite)
    DoglegLength: float = proxy_property(float,'DoglegLength',AccessMode.ReadWrite)
    LandingGap: float = proxy_property(float,'LandingGap',AccessMode.ReadWrite)
    LeaderCount: int = proxy_property(int,'LeaderCount',AccessMode.ReadOnly)
    LeaderLineColor: AcadAcCmColor = proxy_property('AcadAcCmColor','LeaderLineColor',AccessMode.ReadWrite)
    LeaderLinetype: str = proxy_property(str,'LeaderLinetype',AccessMode.ReadWrite)
    LeaderLineWeight: AcLineWeight = proxy_property('AcLineWeight','LeaderLineWeight',AccessMode.ReadWrite)
    LeaderType: AcMLeaderType = proxy_property('AcMLeaderType','LeaderType',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    StyleName: str = proxy_property(str,'StyleName',AccessMode.ReadWrite)
    TextAttachmentDirection: AcTextAttachmentDirection = proxy_property('AcTextAttachmentDirection','TextAttachmentDirection',AccessMode.ReadWrite)
    TextBackgroundFill: bool = proxy_property(bool,'TextBackgroundFill',AccessMode.ReadWrite)
    TextBottomAttachmentType: AcVerticalTextAttachmentType = proxy_property('AcVerticalTextAttachmentType','TextBottomAttachmentType',AccessMode.ReadWrite)
    TextDirection: AcDrawingDirection = proxy_property('AcDrawingDirection','TextDirection',AccessMode.ReadWrite)
    TextFrameDisplay: bool = proxy_property(bool,'TextFrameDisplay',AccessMode.ReadWrite)
    TextHeight: float = proxy_property(float,'TextHeight',AccessMode.ReadWrite)
    TextJustify: AcAttachmentPoint = proxy_property('AcAttachmentPoint','TextJustify',AccessMode.ReadWrite)
    TextLeftAttachmentType: AcTextAttachmentType = proxy_property('AcTextAttachmentType','TextLeftAttachmentType',AccessMode.ReadWrite)
    TextLineSpacingDistance: float = proxy_property(float,'TextLineSpacingDistance',AccessMode.ReadWrite)
    TextLineSpacingFactor: float = proxy_property(float,'TextLineSpacingFactor',AccessMode.ReadWrite)
    TextLineSpacingStyle: AcLineSpacingStyle = proxy_property('AcLineSpacingStyle','TextLineSpacingStyle',AccessMode.ReadWrite)
    TextRightAttachmentType: AcTextAttachmentType = proxy_property('AcTextAttachmentType','TextRightAttachmentType',AccessMode.ReadWrite)
    TextRotation: float = proxy_property(float,'TextRotation',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    TextStyleName: str = proxy_property(str,'TextStyleName',AccessMode.ReadWrite)
    TextTopAttachmentType: AcVerticalTextAttachmentType = proxy_property('AcVerticalTextAttachmentType','TextTopAttachmentType',AccessMode.ReadWrite)
    TextWidth: float = proxy_property(float,'TextWidth',AccessMode.ReadWrite)
    Type: AcLeaderType = proxy_property('AcLeaderType','Type',AccessMode.ReadWrite)

    def AddLeader(self) -> AcadLeader:
        return AcadLeader(self._obj.AddLeader())

    def AddLeaderLine(self, leaderIndex: int, pointArray: PyGePoint3dArray) -> int:
        return self._obj.AddLeaderLine(leaderIndex, pointArray())

    def AddLeaderLineEx(self, pointArray: PyGePoint3dArray) -> int:
        return self._obj.AddLeaderLineEx(pointArray())

    def Evaluate(self) -> None:
        self._obj.Evaluate()
    
    def GetBlockAttributeValue(self, attdefId: int) -> str:
        return self._obj.GetBlockAttributeValue(attdefId)

    def GetDoglegDirection(self, leaderIndex: int) -> PyGeVector3d:
        return PyGeVector3d(self._obj.GetDoglegDirection(leaderIndex))
    
    def GetLeaderIndex(self, leaderLineIndex: int) -> int:
        return self._obj.GetLeaderIndex(leaderLineIndex)
        
    def GetLeaderLineIndexes(self, leaderIndex: int) -> vDoubleArray:
        return vDoubleArray(self._obj.GetLeaderLineIndexes(leaderIndex))

    def GetLeaderLineVertices(self, leaderLineIndex: int) -> PyGePoint3dArray:
        return PyGePoint3dArray(self._obj.GetLeaderLineVertices(leaderLineIndex))

    def GetVertexCount(self, leaderLineIndex: int) -> int:
        return self._obj.GetVertexCount(leaderLineIndex)
    
    def RemoveLeader(self, leaderIndex: int) -> None:
        self._obj.RemoveLeader(leaderIndex)

    def RemoveLeaderLine(self, leaderLineIndex: int) -> None:
        self._obj.RemoveLeaderLine(leaderLineIndex)

    def SetBlockAttributeValue(self, attdefId: int, value: str) -> None:
        self._obj.SetBlockAttributeValue(attdefId, value)

    def SetDoglegDirection(self, leaderIndex: int, dirVec: vDoubleArray) -> None:
        self._obj.SetDoglegDirection(leaderIndex, dirVec())
        
    def SetLeaderLineVertices(self, leaderLineIndex: int, pointArray: PyGePoint3dArray) -> None:
        self._obj.SetLeaderLineVertices(leaderLineIndex, pointArray())
