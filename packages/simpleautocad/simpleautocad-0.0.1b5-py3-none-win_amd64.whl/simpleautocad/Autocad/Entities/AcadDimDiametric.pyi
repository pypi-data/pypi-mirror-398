from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension as AcadDimension

class AcadDimDiametric(AcadDimension):
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
    Arrowhead1Block: str
    Arrowhead1Type: AcDimArrowheadType
    Arrowhead2Block: str
    Arrowhead2Type: AcDimArrowheadType
    ArrowheadSize: int
    CenterMarkSize: float
    CenterType: AcDimCenterType
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
    Fit: AcDimFit
    ForceLineInside: bool
    FractionFormat: AcDimFractionType
    LeaderLength: float
    LinearScaleFactor: float
    Measurement: float
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
    def Copy(self) -> AcadDimDiametric: ...
