from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadMLeaderStyle(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    AlignSpace: int = proxy_property(int,'AlignSpace',AccessMode.ReadWrite)
    Annotative: bool = proxy_property(bool,'Annotative',AccessMode.ReadWrite)
    ArrowSize: int = proxy_property(int,'ArrowSize',AccessMode.ReadWrite)
    ArrowSymbol: str = proxy_property('uArrowSymbol','ArrowSymbol',AccessMode.ReadWrite)
    BitFlags: int = proxy_property(int,'BitFlags',AccessMode.ReadWrite)
    Block: str = proxy_property(str,'Block',AccessMode.ReadOnly)
    BlockColor: AcadAcCmColor = proxy_property('AcadAcCmColor','BlockColor',AccessMode.ReadWrite)
    BlockConnectionType: AcBlockConnectionType = proxy_property('AcBlockConnectionType','BlockConnectionType',AccessMode.ReadWrite)
    BlockRotation: float = proxy_property(float,'BlockRotation',AccessMode.ReadWrite)
    BlockScale: float = proxy_property(float,'BlockScale',AccessMode.ReadWrite)
    BreakSize: float = proxy_property(float,'BreakSize',AccessMode.ReadWrite)
    ContentType: AcMLeaderContentType = proxy_property('AcMLeaderContentType','ContentType',AccessMode.ReadWrite)
    Description: str = proxy_property(str,'Description',AccessMode.ReadWrite)
    DoglegLength: float = proxy_property(float,'DoglegLength',AccessMode.ReadWrite)
    DrawLeaderOrderType: AcDrawLeaderOrderType = proxy_property('AcDrawLeaderOrderType','DrawLeaderOrderType',AccessMode.ReadWrite)
    DrawMLeaderOrderType: AcDrawLeaderOrderType = proxy_property('AcDrawLeaderOrderType','DrawMLeaderOrderType',AccessMode.ReadWrite)
    EnableBlockRotation: bool = proxy_property(bool,'EnableBlockRotation',AccessMode.ReadWrite)
    EnableBlockScale: bool = proxy_property(bool,'EnableBlockScale',AccessMode.ReadWrite)
    EnableDogleg: bool = proxy_property(bool,'EnableDogleg',AccessMode.ReadWrite)
    EnableFrameText: bool = proxy_property(bool,'EnableFrameText',AccessMode.ReadWrite)
    EnableLanding: bool = proxy_property(bool,'EnableLanding',AccessMode.ReadWrite)
    FirstSegmentAngleConstraint: int = proxy_property(int,'FirstSegmentAngleConstraint',AccessMode.ReadWrite)
    LandingGap: float = proxy_property(float,'LandingGap',AccessMode.ReadWrite)
    LeaderLineColor: AcadAcCmColor = proxy_property('AcadAcCmColor','LeaderLineColor',AccessMode.ReadWrite)
    LeaderLinetype: str = proxy_property(str,'LeaderLinetype',AccessMode.ReadWrite)
    LeaderLineTypeId: int = proxy_property(int,'LeaderLineTypeId',AccessMode.ReadWrite)
    LeaderLineWeight: AcLineWeight = proxy_property('AcLineWeight','LeaderLineWeight',AccessMode.ReadWrite)
    MaxLeaderSegmentsPoints: int = proxy_property(int,'MaxLeaderSegmentsPoints',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    OverwritePropChanged: bool = proxy_property(bool,'OverwritePropChanged',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    SecondSegmentAngleConstraint: int = proxy_property(int,'SecondSegmentAngleConstraint',AccessMode.ReadWrite)
    TextAlignmentType: AcTextAlignmentType = proxy_property('AcTextAlignmentType','TextAlignmentType',AccessMode.ReadWrite)
    TextAngleType: AcTextAngleType = proxy_property('AcTextAngleType','TextAngleType',AccessMode.ReadWrite)
    TextAttachmentDirection: AcTextAttachmentDirection = proxy_property('AcTextAttachmentDirection','TextAttachmentDirection',AccessMode.ReadWrite)
    TextBottomAttachmentType: AcVerticalTextAttachmentType = proxy_property('AcVerticalTextAttachmentType','TextBottomAttachmentType',AccessMode.ReadWrite)
    TextColor: AcColor = proxy_property('AcColor','TextBottomAttachmentType',AccessMode.ReadWrite)
    TextHeight: float = proxy_property(float,'TextHeight',AccessMode.ReadWrite)
    TextLeftAttachmentType: AcTextAttachmentType = proxy_property('AcTextAttachmentType','TextLeftAttachmentType',AccessMode.ReadWrite)
    TextRightAttachmentType: AcTextAttachmentType = proxy_property('AcTextAttachmentType','TextRightAttachmentType',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    TextStyle: str = proxy_property(str,'TextStyle',AccessMode.ReadWrite)
    TextTopAttachmentType: AcVerticalTextAttachmentType = proxy_property('AcVerticalTextAttachmentType','TextTopAttachmentType',AccessMode.ReadWrite)

    def GetBoundingBox(self) -> PyGePoint3dArray:
        MinPoint, MaxPoint = self._obj.GetBoundingBox()
        return PyGePoint3dArray(MinPoint, MaxPoint)