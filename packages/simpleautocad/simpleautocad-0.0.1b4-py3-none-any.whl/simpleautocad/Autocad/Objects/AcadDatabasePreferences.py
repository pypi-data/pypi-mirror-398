from __future__ import annotations
from ..Base import *
from ..Proxy import *
# from ..AcadObject import *

class AcadDatabasePreferences(AppObject):
    def __init__(self, obj): super().__init__(obj)

    AllowLongSymbolNames: bool = proxy_property(bool,'AllowLongSymbolNames',AccessMode.ReadWrite)
    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    ContourLinesPerSurface: int = proxy_property(int,'ContourLinesPerSurface',AccessMode.ReadWrite)
    DisplaySilhouette: bool = proxy_property(bool,'DisplaySilhouette',AccessMode.ReadWrite)
    Lineweight: AcLineWeight = proxy_property('AcLineWeight','Lineweight',AccessMode.ReadWrite)
    LineweightDisplay: bool = proxy_property(bool,'LineweightDisplay',AccessMode.ReadWrite)
    ObjectSortByPlotting: bool = proxy_property(bool,'ObjectSortByPlotting',AccessMode.ReadWrite)
    ObjectSortByPSOutput: bool = proxy_property(bool,'ObjectSortByPSOutput',AccessMode.ReadWrite)
    ObjectSortByRedraws: bool = proxy_property(bool,'ObjectSortByRedraws',AccessMode.ReadWrite)
    ObjectSortByRegens: bool = proxy_property(bool,'ObjectSortByRegens',AccessMode.ReadWrite)
    ObjectSortBySelection: bool = proxy_property(bool,'ObjectSortBySelection',AccessMode.ReadWrite)
    ObjectSortBySnap: bool = proxy_property(bool,'ObjectSortBySnap',AccessMode.ReadWrite)
    OLELaunch: bool = proxy_property(bool,'OLELaunch',AccessMode.ReadWrite)
    RenderSmoothness: float = proxy_property(float,'RenderSmoothness',AccessMode.ReadWrite)
    SegmentPerPolyline: int = proxy_property(int,'SegmentPerPolyline',AccessMode.ReadWrite)
    SolidFill: bool = proxy_property(bool,'SolidFill',AccessMode.ReadWrite)
    TextFrameDisplay: bool = proxy_property(bool,'TextFrameDisplay',AccessMode.ReadWrite)
    XRefEdit: bool = proxy_property(bool,'XRefEdit',AccessMode.ReadWrite)
    XRefLayerVisibility: bool = proxy_property(bool,'XRefLayerVisibility',AccessMode.ReadWrite)
    