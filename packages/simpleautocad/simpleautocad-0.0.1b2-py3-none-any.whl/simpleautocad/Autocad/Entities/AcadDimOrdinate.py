from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadDimension import AcadDimension



class AcadDimOrdinate(AcadDimension):
    def __init__(self, obj) -> None: super().__init__(obj)

    AltRoundDistance: float = proxy_property(float,'AltRoundDistance',AccessMode.ReadWrite)
    AltSubUnitsFactor: float = proxy_property(float,'AltSubUnitsFactor',AccessMode.ReadWrite)
    AltSubUnitsSuffix: str = proxy_property(str,'AltSubUnitsSuffix',AccessMode.ReadWrite)
    AltSuppressLeadingZeros: bool = proxy_property(bool,'AltSuppressLeadingZeros',AccessMode.ReadWrite)
    AltSuppressTrailingZeros: bool = proxy_property(bool,'AltSuppressTrailingZeros',AccessMode.ReadWrite)
    AltSuppressZeroFeet: bool = proxy_property(bool,'AltSuppressZeroFeet',AccessMode.ReadWrite)
    AltSuppressZeroInches: bool = proxy_property(bool,'AltSuppressZeroInches',AccessMode.ReadWrite)
    AltTextPrefix: str = proxy_property(str,'AltTextPrefix',AccessMode.ReadWrite)
    AltTextSuffix: str = proxy_property(str,'AltTextSuffix',AccessMode.ReadWrite)
    AltTolerancePrecision: AcDimPrecision = proxy_property('AcDimPrecision','AltTolerancePrecision',AccessMode.ReadWrite)
    AltToleranceSuppressLeadingZeros: bool = proxy_property(bool,'AltToleranceSuppressLeadingZeros',AccessMode.ReadWrite)
    AltToleranceSuppressTrailingZeros: bool = proxy_property(bool,'AltToleranceSuppressTrailingZeros',AccessMode.ReadWrite)
    AltToleranceSuppressZeroFeet: bool = proxy_property(bool,'AltToleranceSuppressZeroFeet',AccessMode.ReadWrite)
    AltToleranceSuppressZeroInches: bool = proxy_property(bool,'AltToleranceSuppressZeroInches',AccessMode.ReadWrite)
    AltUnits: bool = proxy_property(bool,'AltUnits',AccessMode.ReadWrite)
    AltUnitsFormat: AcDimUnits = proxy_property('AcDimUnits','AltUnitsFormat',AccessMode.ReadWrite)
    AltUnitsPrecision: AcDimPrecision = proxy_property('AcDimPrecision','AltUnitsPrecision',AccessMode.ReadWrite)
    AltUnitsScale: float = proxy_property(float,'AltUnitsScale',AccessMode.ReadWrite)
    ArrowheadSize: int = proxy_property(int,'ArrowheadSize',AccessMode.ReadWrite)
    ExtensionLineColor: AcColor = proxy_property('AcColor','ExtensionLineColor',AccessMode.ReadWrite)
    ExtensionLineOffset: float = proxy_property(float,'ExtensionLineOffset',AccessMode.ReadWrite)
    ExtensionLineWeight: AcLineWeight = proxy_property('AcLineWeight','ExtensionLineWeight',AccessMode.ReadWrite)
    ExtLineFixedLen: float = proxy_property(float,'ExtLineFixedLen',AccessMode.ReadWrite)
    ExtLineFixedLenSuppress: bool = proxy_property(bool,'ExtLineFixedLenSuppress',AccessMode.ReadWrite)
    FractionFormat: AcDimFractionType = proxy_property('AcDimFractionType','FractionFormat',AccessMode.ReadWrite)
    LinearScaleFactor: float = proxy_property(float,'LinearScaleFactor',AccessMode.ReadWrite)
    Measurement: float = proxy_property(float,'Measurement',AccessMode.ReadOnly)
    PrimaryUnitsPrecision: AcDimPrecision = proxy_property('AcDimPrecision','PrimaryUnitsPrecision',AccessMode.ReadWrite)
    RoundDistance: float = proxy_property(float,'RoundDistance',AccessMode.ReadWrite)
    SubUnitsFactor: float = proxy_property(float,'SubUnitsFactor',AccessMode.ReadWrite)
    SubUnitsSuffix: str = proxy_property(str,'SubUnitsSuffix',AccessMode.ReadWrite)
    SuppressZeroFeet: bool = proxy_property(bool,'SuppressZeroFeet',AccessMode.ReadWrite)
    SuppressZeroInches: bool = proxy_property(bool,'SuppressZeroInches',AccessMode.ReadWrite)
    ToleranceSuppressZeroFeet: bool = proxy_property(bool,'ToleranceSuppressZeroFeet',AccessMode.ReadWrite)
    ToleranceSuppressZeroInches: bool = proxy_property(bool,'ToleranceSuppressZeroInches',AccessMode.ReadWrite)
    UnitsFormat: AcDimLUnits = proxy_property('AcDimLUnits','UnitsFormat',AccessMode.ReadWrite)

    def Copy(self) -> AcadDimOrdinate:
        return AcadDimOrdinate(self._obj.Copy())