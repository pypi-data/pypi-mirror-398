from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension



class AcadDimAngular(AcadDimension):
    def __init__(self, obj) -> None: super().__init__(obj)

    AngleFormat: AcAngleUnits = proxy_property('AcAngleUnits','AngleFormat',AccessMode.ReadWrite)
    AngleVertex: PyGePoint3d = proxy_property('PyGePoint3d','AngleFormat',AccessMode.ReadWrite)
    Arrowhead1Block: str = proxy_property(str,'Arrowhead1Block',AccessMode.ReadWrite)
    Arrowhead1Type: AcDimArrowheadType = proxy_property('AcDimArrowheadType','Arrowhead1Type',AccessMode.ReadWrite)
    Arrowhead2Block: str = proxy_property(str,'Arrowhead2Block',AccessMode.ReadWrite)
    Arrowhead2Type: AcDimArrowheadType = proxy_property('AcDimArrowheadType','Arrowhead2Type',AccessMode.ReadWrite)
    ArrowheadSize: int = proxy_property(int,'ArrowheadSize',AccessMode.ReadWrite)
    DimConstrDesc: str = proxy_property(str,'DimConstrDesc',AccessMode.ReadWrite)
    DimConstrExpression: str = proxy_property(str,'DimConstrExpression',AccessMode.ReadWrite)
    DimConstrForm: bool = proxy_property(bool,'DimConstrForm',AccessMode.ReadWrite)
    DimConstrName: str = proxy_property(str,'DimConstrName',AccessMode.ReadWrite)
    DimConstrReference: bool = proxy_property(bool,'DimConstrReference',AccessMode.ReadWrite)
    DimConstrValue: str = proxy_property(str,'DimConstrValue',AccessMode.ReadWrite)
    DimensionLineColor: AcColor = proxy_property('AcColor','DimensionLineColor',AccessMode.ReadWrite)
    DimensionLinetype: str = proxy_property(str,'DimensionLinetype',AccessMode.ReadWrite)
    DimensionLineWeight: AcLineWeight = proxy_property('AcLineWeight','DimensionLineWeight',AccessMode.ReadWrite)
    DimLine1Suppress: bool = proxy_property(bool,'DimLine1Suppress',AccessMode.ReadWrite)
    DimLine2Suppress: bool = proxy_property(bool,'DimLine2Suppress',AccessMode.ReadWrite)
    DimLineInside: bool = proxy_property(bool,'DimLineInside',AccessMode.ReadWrite)
    ExtensionLineColor: AcColor = proxy_property('AcColor','ExtensionLineColor',AccessMode.ReadWrite)
    ExtensionLineExtend: float = proxy_property(float,'ExtensionLineExtend',AccessMode.ReadWrite)
    ExtensionLineOffset: float = proxy_property(float,'ExtensionLineOffset',AccessMode.ReadWrite)
    ExtensionLineWeight: AcLineWeight = proxy_property('AcLineWeight','ExtensionLineWeight',AccessMode.ReadWrite)
    ExtLine1EndPoint: PyGePoint3d = proxy_property('PyGePoint3d','ExtLine1EndPoint',AccessMode.ReadWrite)
    ExtLine1Linetype: str = proxy_property(str,'ExtLine1Linetype',AccessMode.ReadWrite)
    ExtLine1StartPoint: PyGePoint3d = proxy_property('PyGePoint3d','ExtLine1StartPoint',AccessMode.ReadWrite)
    ExtLine1Suppress: bool = proxy_property(bool,'ExtLine1Suppress',AccessMode.ReadWrite)
    ExtLine2EndPoint: PyGePoint3d = proxy_property('PyGePoint3d','ExtLine2EndPoint',AccessMode.ReadWrite)
    ExtLine2Linetype: str = proxy_property(str,'ExtLine2Linetype',AccessMode.ReadWrite)
    ExtLine2StartPoint: PyGePoint3d = proxy_property('PyGePoint3d','ExtLine2StartPoint',AccessMode.ReadWrite)
    ExtLine2Suppress: bool = proxy_property(bool,'ExtLine2Suppress',AccessMode.ReadWrite)
    ExtLineFixedLen: float = proxy_property(float,'ExtLineFixedLen',AccessMode.ReadWrite)
    ExtLineFixedLenSuppress: bool = proxy_property(bool,'ExtLineFixedLenSuppress',AccessMode.ReadWrite)
    Fit: AcDimFit = proxy_property('AcDimFit','Fit',AccessMode.ReadWrite)
    ForceLineInside: bool = proxy_property(bool,'ForceLineInside',AccessMode.ReadWrite)
    HorizontalTextPosition: AcDimHorizontalJustification = proxy_property('AcDimHorizontalJustification','HorizontalTextPosition',AccessMode.ReadWrite)
    Measurement: float = proxy_property(float,'Measurement',AccessMode.ReadOnly)
    TextInside: bool = proxy_property(bool,'TextInside',AccessMode.ReadWrite)
    TextInsideAlign: bool = proxy_property(bool,'TextInsideAlign',AccessMode.ReadWrite)
    TextOutsideAlign: bool = proxy_property(bool,'TextOutsideAlign',AccessMode.ReadWrite)
    TextPrecision: AcDimPrecision = proxy_property('AcDimPrecision','TextPrecision',AccessMode.ReadWrite)

    def Copy(self) -> AcadDimAngular:
        return AcadDimAngular(self._obj.Copy())