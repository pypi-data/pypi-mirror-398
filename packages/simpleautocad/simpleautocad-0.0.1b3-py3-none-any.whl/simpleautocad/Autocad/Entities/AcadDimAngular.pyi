from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension as AcadDimension

class AcadDimAngular(AcadDimension):
    def __init__(self, obj) -> None: ...
    AngleFormat: AcAngleUnits
    AngleVertex: PyGePoint3d
    Arrowhead1Block: str
    Arrowhead1Type: AcDimArrowheadType
    Arrowhead2Block: str
    Arrowhead2Type: AcDimArrowheadType
    ArrowheadSize: int
    DimConstrDesc: str
    DimConstrExpression: str
    DimConstrForm: bool
    DimConstrName: str
    DimConstrReference: bool
    DimConstrValue: str
    DimensionLineColor: AcColor
    DimensionLinetype: str
    DimensionLineWeight: AcLineWeight
    DimLine1Suppress: bool
    DimLine2Suppress: bool
    DimLineInside: bool
    ExtensionLineColor: AcColor
    ExtensionLineExtend: float
    ExtensionLineOffset: float
    ExtensionLineWeight: AcLineWeight
    ExtLine1EndPoint: PyGePoint3d
    ExtLine1Linetype: str
    ExtLine1StartPoint: PyGePoint3d
    ExtLine1Suppress: bool
    ExtLine2EndPoint: PyGePoint3d
    ExtLine2Linetype: str
    ExtLine2StartPoint: PyGePoint3d
    ExtLine2Suppress: bool
    ExtLineFixedLen: float
    ExtLineFixedLenSuppress: bool
    Fit: AcDimFit
    ForceLineInside: bool
    HorizontalTextPosition: AcDimHorizontalJustification
    Measurement: float
    TextInside: bool
    TextInsideAlign: bool
    TextOutsideAlign: bool
    TextPrecision: AcDimPrecision
    def Copy(self) -> AcadDimAngular: ...
