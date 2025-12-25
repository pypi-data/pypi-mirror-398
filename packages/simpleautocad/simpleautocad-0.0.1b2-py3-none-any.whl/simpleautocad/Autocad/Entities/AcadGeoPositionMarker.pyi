from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadGeoPositionMarker(AcadEntity):
    def __init__(self, obj) -> None: ...
    Altitude: float
    BackgroundFill: bool
    DrawingDirection: AcDrawingDirection
    Height: float
    LandingGap: float
    Latitude: str
    LineSpacingDistance: float
    LineSpacingFactor: float
    LineSpacingStyle: AcLineSpacingStyle
    Longitude: str
    Notes: str
    Position: PyGePoint3d
    Radius: float
    Rotation: float
    TextFrameDisplay: bool
    TextJustify: AcAttachmentPoint
    TextString: str
    TextStyleName: str
    TextWidth: float
    def Copy(self) -> AcadGeoPositionMarker: ...
