from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPointCloudEx(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    ColorScheme: str = proxy_property(str,'ColorScheme',AccessMode.ReadWrite)
    Geolocate: bool = proxy_property(bool,'Geolocate',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    Locked: bool = proxy_property(bool,'Locked',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Path: str = proxy_property(str,'Path',AccessMode.ReadOnly)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    Scale: float = proxy_property(float,'Scale',AccessMode.ReadWrite)
    Segmentation: str = proxy_property(str,'Segmentation',AccessMode.ReadOnly)
    ShowCropped: bool = proxy_property(bool,'ShowCropped',AccessMode.ReadWrite)
    Stylization: AcPointCloudExStylizationType = proxy_property('AcPointCloudExStylizationType','Stylization',AccessMode.ReadWrite)
    Unit: str = proxy_property(str,'Unit',AccessMode.ReadOnly)
    UnitFactor: str = proxy_property(str,'UnitFactor',AccessMode.ReadOnly)

    def Copy(self) -> AcadPointCloudEx:
        return AcadPointCloudEx(self._obj.Copy())