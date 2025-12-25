from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import AcadObject



class AcadDimStyle(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)

    def CopyFrom(self, SourceObject: AcadDimStyle|
                                        AcadDim3PointAngular|
                                        AcadDimAligned|
                                        AcadDimAngular|
                                        AcadDimArcLength|
                                        AcadDimDiametric|
                                        AcadDimOrdinate|
                                        AcadDimRadial|
                                        AcadDimRadialLarge|
                                        AcadDimRotated|
                                        AcadDocument|
                                        AcadLayout|
                                        AcadLeader|
                                        AcadPlotConfiguration) -> None: 
        self._obj.CopyFrom(SourceObject)
