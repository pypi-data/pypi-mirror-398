from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension as AcadDimension

class AcadDimOrdinate(AcadDimension):
    def __init__(self, obj) -> None: ...
    AltRoundDistance: float
    AltSubUnitsFactor: float
    AltSubUnitsSuffix: str
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
    ArrowheadSize: int
    ExtensionLineColor: AcColor
    ExtensionLineOffset: float
    ExtensionLineWeight: AcLineWeight
    ExtLineFixedLen: float
    ExtLineFixedLenSuppress: bool
    FractionFormat: AcDimFractionType
    LinearScaleFactor: float
    Measurement: float
    PrimaryUnitsPrecision: AcDimPrecision
    RoundDistance: float
    SubUnitsFactor: float
    SubUnitsSuffix: str
    SuppressZeroFeet: bool
    SuppressZeroInches: bool
    ToleranceSuppressZeroFeet: bool
    ToleranceSuppressZeroInches: bool
    UnitsFormat: AcDimLUnits
    def Copy(self) -> AcadDimOrdinate: ...
