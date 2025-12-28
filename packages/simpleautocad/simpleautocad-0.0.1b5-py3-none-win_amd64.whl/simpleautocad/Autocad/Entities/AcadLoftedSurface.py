from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadLoftedSurface(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Closed: bool = proxy_property(bool,'Closed',AccessMode.ReadWrite)
    EdgeExtensionDistances: Variant = proxy_property(Variant,'EdgeExtensionDistances',AccessMode.ReadWrite)
    EndDraftAngle: float = proxy_property(float,'EndDraftAngle',AccessMode.ReadWrite)
    EndDraftMagnitude: int = proxy_property(int,'EndDraftMagnitude',AccessMode.ReadWrite)
    EndSmoothContinuity: int = proxy_property(int,'EndSmoothContinuity',AccessMode.ReadWrite)
    EndSmoothMagnitude: float = proxy_property(float,'EndSmoothMagnitude',AccessMode.ReadWrite)
    MaintainAssociativity: int = proxy_property(int,'MaintainAssociativity',AccessMode.ReadWrite)
    NumCrossSections: int = proxy_property(int,'NumCrossSections',AccessMode.ReadWrite)
    NumGuidePaths: int = proxy_property(int,'NumGuidePaths',AccessMode.WriteOnly)
    Periodic: bool = proxy_property(bool,'Periodic',AccessMode.ReadWrite)
    ShowAssociativity: bool = proxy_property(bool,'ShowAssociativity',AccessMode.ReadWrite)
    StartDraftAngle: float = proxy_property(float,'StartDraftAngle',AccessMode.ReadWrite)
    StartDraftMagnitude: int = proxy_property(int,'StartDraftMagnitude',AccessMode.ReadWrite)
    StartSmoothContinuity: int = proxy_property(int,'StartSmoothContinuity',AccessMode.ReadWrite)
    StartSmoothMagnitude: float = proxy_property(float,'StartSmoothMagnitude',AccessMode.ReadWrite)
    SurfaceNormals: int = proxy_property(int,'SurfaceNormals',AccessMode.ReadWrite)
    SurfaceType: str = proxy_property(str,'SurfaceType',AccessMode.ReadOnly)
    SurfTrimAssociativity: bool = proxy_property(Variant,'SurfTrimAssociativity',AccessMode.ReadWrite)
    UIsolineDensity: int = proxy_property(int,'UIsolineDensity',AccessMode.ReadWrite)
    VIsolineDensity: int = proxy_property(int,'VIsolineDensity',AccessMode.ReadWrite)
    WireframeType: AcWireframeType = proxy_property('AcWireframeType','WireframeType',AccessMode.ReadWrite)

    def Copy(self) -> AcadLoftedSurface:
        return AcadLoftedSurface(self._obj.Copy())