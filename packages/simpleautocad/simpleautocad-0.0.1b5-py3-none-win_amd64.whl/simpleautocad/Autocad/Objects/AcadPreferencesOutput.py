from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesOutput(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    AutomaticPlotLog: bool = proxy_property(bool,'AutomaticPlotLog',AccessMode.ReadWrite)
    ContinuousPlotLog: bool = proxy_property(bool,'ContinuousPlotLog',AccessMode.ReadWrite)
    DefaultOutputDevice: bool = proxy_property(bool,'DefaultOutputDevice',AccessMode.ReadWrite)
    DefaultPlotStyleForLayer: str = proxy_property(str,'DefaultPlotStyleForLayer',AccessMode.ReadWrite)
    DefaultPlotStyleForObjects: str = proxy_property(str,'DefaultPlotStyleForObjects',AccessMode.ReadWrite)
    DefaultPlotStyleTable: str = proxy_property(str,'DefaultPlotStyleTable',AccessMode.ReadWrite)
    DefaultPlotToFilePath: str = proxy_property(str,'DefaultPlotToFilePath',AccessMode.ReadWrite)
    OLEQuality: AcOleQuality  = proxy_property('AcOleQuality','OLEQuality',AccessMode.ReadWrite)
    PlotLegacy: bool  = proxy_property(bool,'PlotLegacy',AccessMode.ReadWrite)
    PlotPolicy: AcPlotPolicy   = proxy_property('AcPlotPolicy','PlotPolicy',AccessMode.ReadWrite)
    PrinterPaperSizeAlert: bool   = proxy_property(bool,'PrinterPaperSizeAlert',AccessMode.ReadWrite)
    UseLastPlotSettings: bool   = proxy_property(bool,'UseLastPlotSettings',AccessMode.ReadWrite)