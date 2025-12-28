from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadPointCloudEx(AcadEntity):
    def __init__(self, obj) -> None: ...
    ColorScheme: str
    Geolocate: bool
    InsertionPoint: PyGePoint3d
    Locked: bool
    Name: str
    Path: str
    Rotation: float
    Scale: float
    Segmentation: str
    ShowCropped: bool
    Stylization: AcPointCloudExStylizationType
    Unit: str
    UnitFactor: str
    def Copy(self) -> AcadPointCloudEx: ...
