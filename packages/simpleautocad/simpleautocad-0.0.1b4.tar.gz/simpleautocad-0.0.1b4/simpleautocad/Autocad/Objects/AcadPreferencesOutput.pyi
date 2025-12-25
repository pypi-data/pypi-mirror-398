from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesOutput(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    AutomaticPlotLog: bool
    ContinuousPlotLog: bool
    DefaultOutputDevice: bool
    DefaultPlotStyleForLayer: str
    DefaultPlotStyleForObjects: str
    DefaultPlotStyleTable: str
    DefaultPlotToFilePath: str
    OLEQuality: AcOleQuality
    PlotLegacy: bool
    PlotPolicy: AcPlotPolicy
    PrinterPaperSizeAlert: bool
    UseLastPlotSettings: bool
