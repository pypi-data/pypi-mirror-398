from ..Base import *
from ..Proxy import *

class AcadDatabasePreferences(AppObject):
    def __init__(self, obj) -> None: ...
    AllowLongSymbolNames: bool
    Application: AcadApplication
    ContourLinesPerSurface: int
    DisplaySilhouette: bool
    Lineweight: AcLineWeight
    LineweightDisplay: bool
    ObjectSortByPlotting: bool
    ObjectSortByPSOutput: bool
    ObjectSortByRedraws: bool
    ObjectSortByRegens: bool
    ObjectSortBySelection: bool
    ObjectSortBySnap: bool
    OLELaunch: bool
    RenderSmoothness: float
    SegmentPerPolyline: int
    SolidFill: bool
    TextFrameDisplay: bool
    XRefEdit: bool
    XRefLayerVisibility: bool
