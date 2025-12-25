from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPointCloud(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    IntensityColorScheme: AcPointCloudIntensityStyle = proxy_property('AcPointCloudIntensityStyle','IntensityColorScheme',AccessMode.ReadWrite)
    Locked: bool = proxy_property(bool,'Locked',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Path: str = proxy_property(str,'Path',AccessMode.ReadOnly)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    Scale: float = proxy_property(float,'Scale',AccessMode.ReadWrite)
    ShowClipped: bool = proxy_property(bool,'ShowClipped',AccessMode.ReadWrite)
    ShowIntensity: bool = proxy_property(bool,'ShowIntensity',AccessMode.ReadWrite)
    Stylization: AcPointCloudStylizationType = proxy_property('AcPointCloudStylizationType','Stylization',AccessMode.ReadWrite)
    Unit: str = proxy_property(str,'Unit',AccessMode.ReadOnly)
    UnitFactor: str = proxy_property(str,'UnitFactor',AccessMode.ReadOnly)
    UseEntityColor: AcPointCloudColorType = proxy_property('AcPointCloudColorType','UseEntityColor',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def Copy(self) -> AcadPointCloud:
        return AcadPointCloud(self._obj.Copy())