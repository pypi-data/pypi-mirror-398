from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension as AcadDimension

class AcadDimRadialLarge(AcadDimension):
    def __init__(self, obj) -> None: ...
    AltRoundDistance: float
    AltSuppressLeadingZeros: bool
    AltSuppressTrailingZeros: bool
    AltSuppressZeroFeet: bool
    AltSuppressZeroInches: bool
    AltTextPrefix: str
    AltTextSuffix: str
    AltTolerancePrecision: AcDimPrecision
    AltToleranceSuppressLeadingZeros: bool
    AltToleranceSuppressTrailingZeros: bool
    AltToleranceSuppressZeroFeet: bool
    AltToleranceSuppressZeroInches: bool
    AltUnits: bool
    AltUnitsFormat: AcDimUnits
    AltUnitsPrecision: AcDimPrecision
    AltUnitsScale: float
    ArrowheadBlock: str
    ArrowheadType: AcDimArrowheadType
    ArrowheadSize: float
    Center: PyGePoint3d
    CenterMarkSize: float
    CenterType: AcDimCenterType
    ChordPoint: PyGePoint3d
    DimensionLineColor: AcColor
    DimensionLineExtend: float
    DimensionLinetype: str
    DimensionLineWeight: AcLineWeight
    DimLineSuppress: bool
    Fit: AcDimFit
    ForceLineInside: bool
    FractionFormat: AcDimFractionType
    JogAngle: float
    JogLocation: PyGePoint3d
    LeaderLength: float
    LinearScaleFactor: float
    Measurement: float
    OverrideCenter: PyGePoint3d
    PrimaryUnitsPrecision: AcDimPrecision
    RoundDistance: float
    SuppressZeroFeet: bool
    SuppressZeroInches: bool
    TextInside: bool
    TextInsideAlign: bool
    TextOutsideAlign: bool
    ToleranceSuppressZeroFeet: bool
    ToleranceSuppressZeroInches: bool
    UnitsFormat: AcDimLUnits
    def Copy(self) -> AcadDimRadialLarge: ...
