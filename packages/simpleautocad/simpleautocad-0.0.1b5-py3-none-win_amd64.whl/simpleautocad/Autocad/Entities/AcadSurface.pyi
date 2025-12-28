from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadSurface(AcadEntity):
    def __init__(self, obj) -> None: ...
    EdgeExtensionDistances: float
    MaintainAssociativity: int
    ShowAssociativity: bool
    SurfaceType: str
    SurfTrimAssociativity: bool
    UIsolineDensity: int
    VIsolineDensity: int
    WireframeType: AcWireframeType
    def Copy(self) -> AcadSurface: ...
