from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadMLeaderStyle(AcadObject):
    def __init__(self, obj) -> None: ...
    AlignSpace: int
    Annotative: bool
    ArrowSize: int
    ArrowSymbol: str
    BitFlags: int
    Block: str
    BlockColor: AcadAcCmColor
    BlockConnectionType: AcBlockConnectionType
    BlockRotation: float
    BlockScale: float
    BreakSize: float
    ContentType: AcMLeaderContentType
    Description: str
    DoglegLength: float
    DrawLeaderOrderType: AcDrawLeaderOrderType
    DrawMLeaderOrderType: AcDrawLeaderOrderType
    EnableBlockRotation: bool
    EnableBlockScale: bool
    EnableDogleg: bool
    EnableFrameText: bool
    EnableLanding: bool
    FirstSegmentAngleConstraint: int
    LandingGap: float
    LeaderLineColor: AcadAcCmColor
    LeaderLinetype: str
    LeaderLineTypeId: int
    LeaderLineWeight: AcLineWeight
    MaxLeaderSegmentsPoints: int
    Name: str
    OverwritePropChanged: bool
    ScaleFactor: float
    SecondSegmentAngleConstraint: int
    TextAlignmentType: AcTextAlignmentType
    TextAngleType: AcTextAngleType
    TextAttachmentDirection: AcTextAttachmentDirection
    TextBottomAttachmentType: AcVerticalTextAttachmentType
    TextColor: AcColor
    TextHeight: float
    TextLeftAttachmentType: AcTextAttachmentType
    TextRightAttachmentType: AcTextAttachmentType
    TextString: str
    TextStyle: str
    TextTopAttachmentType: AcVerticalTextAttachmentType
    def GetBoundingBox(self) -> PyGePoint3dArray: ...
