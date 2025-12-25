from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadLoftedSurface(AcadEntity):
    def __init__(self, obj) -> None: ...
    Closed: bool
    EdgeExtensionDistances: Variant
    EndDraftAngle: float
    EndDraftMagnitude: int
    EndSmoothContinuity: int
    EndSmoothMagnitude: float
    MaintainAssociativity: int
    NumCrossSections: int
    NumGuidePaths: int
    Periodic: bool
    ShowAssociativity: bool
    StartDraftAngle: float
    StartDraftMagnitude: int
    StartSmoothContinuity: int
    StartSmoothMagnitude: float
    SurfaceNormals: int
    SurfaceType: str
    SurfTrimAssociativity: bool
    UIsolineDensity: int
    VIsolineDensity: int
    WireframeType: AcWireframeType
    def Copy(self) -> AcadLoftedSurface: ...
