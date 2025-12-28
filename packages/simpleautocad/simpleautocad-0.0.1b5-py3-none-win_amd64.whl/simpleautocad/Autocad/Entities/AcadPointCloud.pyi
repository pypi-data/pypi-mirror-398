from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadPointCloud(AcadEntity):
    def __init__(self, obj) -> None: ...
    Height: float
    InsertionPoint: PyGePoint3d
    IntensityColorScheme: AcPointCloudIntensityStyle
    Locked: bool
    Name: str
    Path: str
    Rotation: float
    Scale: float
    ShowClipped: bool
    ShowIntensity: bool
    Stylization: AcPointCloudStylizationType
    Unit: str
    UnitFactor: str
    UseEntityColor: AcPointCloudColorType
    Width: float
    def Copy(self) -> AcadPointCloud: ...
