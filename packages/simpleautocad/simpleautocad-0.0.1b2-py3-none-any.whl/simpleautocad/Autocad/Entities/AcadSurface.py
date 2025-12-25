from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadSurface(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    EdgeExtensionDistances: float = proxy_property(float,'EdgeExtensionDistances',AccessMode.ReadWrite)
    MaintainAssociativity: int = proxy_property(int,'MaintainAssociativity',AccessMode.ReadWrite)
    ShowAssociativity: bool = proxy_property(bool,'ShowAssociativity',AccessMode.ReadWrite)
    SurfaceType: str = proxy_property(str,'SurfaceType',AccessMode.ReadOnly)
    SurfTrimAssociativity: bool = proxy_property(bool,'SurfTrimAssociativity',AccessMode.ReadWrite)
    UIsolineDensity: int = proxy_property(int,'UIsolineDensity',AccessMode.ReadWrite)
    VIsolineDensity: int = proxy_property(int,'VIsolineDensity',AccessMode.ReadWrite)
    WireframeType: AcWireframeType = proxy_property('AcWireframeType','WireframeType',AccessMode.ReadWrite)

    def Copy(self) -> AcadSurface:
        return AcadSurface(self._obj.Copy())