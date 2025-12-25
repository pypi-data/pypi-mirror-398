from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadGeoPositionMarker(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Altitude: float = proxy_property(float,'Altitude',AccessMode.ReadWrite)
    BackgroundFill: bool = proxy_property(bool,'BackgroundFill',AccessMode.ReadWrite)
    DrawingDirection: AcDrawingDirection = proxy_property('AcDrawingDirection','DrawingDirection',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    LandingGap: float = proxy_property(float,'LandingGap',AccessMode.ReadWrite)
    Latitude: str = proxy_property(str,'Latitude',AccessMode.ReadWrite)
    LineSpacingDistance: float = proxy_property(float,'LineSpacingDistance',AccessMode.ReadWrite)
    LineSpacingFactor: float = proxy_property(float,'LineSpacingFactor',AccessMode.ReadWrite)
    LineSpacingStyle: AcLineSpacingStyle = proxy_property('AcLineSpacingStyle','LineSpacingStyle',AccessMode.ReadWrite)
    Longitude: str = proxy_property(str,'Longitude',AccessMode.ReadWrite)
    Notes: str = proxy_property(str,'Notes',AccessMode.ReadWrite)
    Position: PyGePoint3d = proxy_property('PyGePoint3d','Position',AccessMode.ReadWrite)
    Radius: float = proxy_property(float,'Radius',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    TextFrameDisplay: bool = proxy_property(bool,'TextFrameDisplay',AccessMode.ReadWrite)
    TextJustify: AcAttachmentPoint = proxy_property('AcAttachmentPoint','TextJustify',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    TextStyleName: str = proxy_property(str,'TextStyleName',AccessMode.ReadWrite)
    TextWidth: float = proxy_property(float,'TextWidth',AccessMode.ReadWrite)

    def Copy(self) -> AcadGeoPositionMarker:
        return AcadGeoPositionMarker(self._obj.Copy())