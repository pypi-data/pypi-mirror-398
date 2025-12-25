from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesDrafting(AppObject):
    def __init__(self, obj) -> None: ...
    AlignmentPointAcquisition: AcAlignmentPointAcquisition
    Application: AcadApplication
    AutoSnapAperture: bool
    AutoSnapApertureSize: int
    AutoSnapMagnet: bool
    AutoSnapMarker: bool
    AutoSnapMarkerColor: AcColor
    AutoSnapMarkerSize: int
    AutoSnapToolTip: bool
    AutoTrackTooltip: bool
    FullScreenTrackingVector: bool
    PolarTrackingVector: bool
