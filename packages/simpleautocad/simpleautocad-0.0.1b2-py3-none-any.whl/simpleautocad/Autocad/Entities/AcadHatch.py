from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadHatch(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    AssociativeHatch: bool = proxy_property(bool,'AssociativeHatch',AccessMode.ReadOnly)
    BackgroundColor: AcadAcCmColor = proxy_property('AcadAcCmColor','BackgroundColor',AccessMode.ReadWrite)
    Elevation: float = proxy_property(float,'Elevation',AccessMode.ReadWrite)
    GradientAngle: float = proxy_property(float,'GradientAngle',AccessMode.ReadWrite)
    GradientCentered: bool = proxy_property(bool,'GradientCentered',AccessMode.ReadWrite)
    GradientColor1: AcadAcCmColor = proxy_property('AcadAcCmColor','GradientColor1',AccessMode.ReadWrite)
    GradientColor2: AcadAcCmColor = proxy_property('AcadAcCmColor','GradieGradientColor2ntCentered',AccessMode.ReadWrite)
    GradientName: str = proxy_property(str,'GradientName',AccessMode.ReadWrite)
    HatchObjectType: AcHatchObjectType = proxy_property('AcHatchObjectType','HatchObjectType',AccessMode.ReadWrite)
    HatchStyle: AcHatchStyle = proxy_property('AcHatchStyle','HatchStyle',AccessMode.ReadWrite)
    ISOPenWidth: AcISOPenWidth = proxy_property('AcISOPenWidth','ISOPenWidth',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    NumberOfLoops: int = proxy_property(int,'NumberOfLoops',AccessMode.ReadOnly)
    Origin: PyGePoint3d = proxy_property('PyGePoint3d','Origin',AccessMode.ReadWrite)
    PatternAngle: float = proxy_property(float,'PatternAngle',AccessMode.ReadWrite)
    PatternDouble: bool = proxy_property(bool,'PatternDouble',AccessMode.ReadWrite)
    PatternName: str = proxy_property(str,'PatternName',AccessMode.ReadWrite)
    PatternScale: float = proxy_property(float,'PatternScale',AccessMode.ReadWrite)
    PatternSpace: float = proxy_property(float,'PatternSpace',AccessMode.ReadWrite)
    PatternType: AcPatternType = proxy_property(AcPatternType,'PatternType',AccessMode.ReadOnly)

    def AppendInnerLoop(self, Loop: vObjectArray[AcadArc|AcadCircle|AcadEllipse|AcadLine|AcadPolyline|AcadRegion|AcadSpline]) -> None:
        self._obj.AppendInnerLoop(Loop())

    def AppendOuterLoop(self, Loop: vObjectArray[AcadArc|AcadCircle|AcadEllipse|AcadLine|AcadPolyline|AcadRegion|AcadSpline]) -> None:
        self._obj.AppendOuterLoop(Loop())
