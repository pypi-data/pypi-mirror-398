from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadDimension(AcadEntity):
    def __init__(self, obj) -> None: ...
    DecimalSeparator: str
    DimTxtDirection: bool
    Normal: PyGeVector3d
    Rotation: float
    ScaleFactor: float
    StyleName: str
    SuppressLeadingZeros: bool
    SuppressTrailingZeros: bool
    TextColor: AcColor
    TextFill: bool
    TextFillColor: AcColor
    TextGap: float
    TextHeight: float
    TextMovement: AcDimTextMovement
    TextOverride: str
    TextPosition: PyGePoint3d
    TextPrefix: str
    TextRotation: float
    TextStyle: str
    TextSuffix: str
    ToleranceDisplay: AcDimToleranceMethod
    ToleranceHeightScale: float
    ToleranceJustification: AcDimToleranceJustify
    ToleranceLowerLimit: float
    TolerancePrecision: AcDimPrecision
    ToleranceSuppressLeadingZeros: bool
    ToleranceSuppressTrailingZeros: bool
    ToleranceUpperLimit: float
    VerticalTextPosition: AcDimVerticalJustification
    def Copy(self) -> AcadDimension: ...
