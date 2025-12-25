from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesDrafting(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    AlignmentPointAcquisition: AcAlignmentPointAcquisition = proxy_property('AcAlignmentPointAcquisition','AlignmentPointAcquisition',AccessMode.ReadWrite)
    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    AutoSnapAperture: bool = proxy_property(bool,'AutoSnapAperture',AccessMode.ReadWrite)
    AutoSnapApertureSize: int = proxy_property(int,'AutoSnapApertureSize',AccessMode.ReadWrite)
    AutoSnapMagnet: bool = proxy_property(bool,'AutoSnapMagnet',AccessMode.ReadWrite)
    AutoSnapMarker: bool = proxy_property(bool,'AutoSnapMarker',AccessMode.ReadWrite)
    AutoSnapMarkerColor: AcColor = proxy_property('AcColor','AutoSnapMarkerColor',AccessMode.ReadWrite)
    AutoSnapMarkerSize: int = proxy_property(int,'AutoSnapMarkerSize',AccessMode.ReadWrite)
    AutoSnapToolTip: bool = proxy_property(bool,'AutoSnapToolTip',AccessMode.ReadWrite)
    AutoTrackTooltip: bool = proxy_property(bool,'AutoTrackTooltip',AccessMode.ReadWrite)
    FullScreenTrackingVector: bool = proxy_property(bool,'FullScreenTrackingVector',AccessMode.ReadWrite)
    PolarTrackingVector: bool = proxy_property(bool,'PolarTrackingVector',AccessMode.ReadWrite)