from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadDimension(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    DecimalSeparator: str = proxy_property(str,'DecimalSeparator',AccessMode.ReadWrite)
    DimTxtDirection: bool = proxy_property(bool,'DimTxtDirection',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    StyleName: str = proxy_property(str,'StyleName',AccessMode.ReadWrite)
    SuppressLeadingZeros: bool = proxy_property(bool,'SuppressLeadingZeros',AccessMode.ReadWrite)
    SuppressTrailingZeros: bool = proxy_property(bool,'SuppressLeadingZeros',AccessMode.ReadWrite)
    TextColor: AcColor = proxy_property('AcColor','TextColor',AccessMode.ReadWrite)
    TextFill: bool = proxy_property(bool,'TextFill',AccessMode.ReadWrite)
    TextFillColor: AcColor = proxy_property('AcColor','TextFillColor',AccessMode.ReadWrite)
    TextGap: float = proxy_property(float,'TextGap',AccessMode.ReadWrite)
    TextHeight: float = proxy_property(float,'TextHeight',AccessMode.ReadWrite)
    TextMovement: AcDimTextMovement = proxy_property('AcDimTextMovement','TextMovement',AccessMode.ReadWrite)
    TextOverride: str = proxy_property(str,'TextOverride',AccessMode.ReadWrite)
    TextPosition: PyGePoint3d = proxy_property('PyGePoint3d','TextPosition',AccessMode.ReadWrite)
    TextPrefix: str = proxy_property(str,'TextPrefix',AccessMode.ReadWrite)
    TextRotation: float = proxy_property(float,'TextRotation',AccessMode.ReadWrite)
    TextStyle: str = proxy_property(str,'TextStyle',AccessMode.ReadWrite)
    TextSuffix: str = proxy_property(str,'TextSuffix',AccessMode.ReadWrite)
    ToleranceDisplay: AcDimToleranceMethod = proxy_property('AcDimToleranceMethod','ToleranceDisplay',AccessMode.ReadWrite)
    ToleranceHeightScale: float = proxy_property(float,'ToleranceHeightScale',AccessMode.ReadWrite)
    ToleranceJustification: AcDimToleranceJustify = proxy_property('AcDimToleranceJustify','ToleranceJustification',AccessMode.ReadWrite)
    ToleranceLowerLimit: float = proxy_property(float,'ToleranceLowerLimit',AccessMode.ReadWrite)
    TolerancePrecision: AcDimPrecision = proxy_property('AcDimPrecision','ToleranceLowerLimit',AccessMode.ReadWrite)
    ToleranceSuppressLeadingZeros: bool = proxy_property(bool,'ToleranceSuppressLeadingZeros',AccessMode.ReadWrite)
    ToleranceSuppressTrailingZeros: bool = proxy_property(bool,'ToleranceSuppressTrailingZeros',AccessMode.ReadWrite)
    ToleranceUpperLimit: float = proxy_property(float,'ToleranceUpperLimit',AccessMode.ReadWrite)
    VerticalTextPosition: AcDimVerticalJustification = proxy_property('AcDimVerticalJustification','VerticalTextPosition',AccessMode.ReadWrite)

    def Copy(self) -> AcadDimension:
        return AcadDimension(self._obj.Copy())



        


