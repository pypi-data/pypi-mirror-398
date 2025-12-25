from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesDisplay(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    AutoTrackingVecColor: int = proxy_property('OLE_COLOR','AutoTrackingVecColor',AccessMode.ReadWrite)
    CursorSize: int = proxy_property(int,'CursorSize',AccessMode.ReadWrite)
    DisplayLayoutTabs: bool = proxy_property(bool,'DisplayLayoutTabs',AccessMode.ReadWrite)
    DisplayScreenMenu: bool = proxy_property(bool,'DisplayScreenMenu',AccessMode.ReadWrite)
    DisplayScrollBars: bool = proxy_property(bool,'DisplayScrollBars',AccessMode.ReadWrite)
    DockedVisibleLines: int = proxy_property(int,'DockedVisibleLines',AccessMode.ReadWrite)
    GraphicsWinLayoutBackgrndColor: int = proxy_property('OLE_COLOR','GraphicsWinLayoutBackgrndColor',AccessMode.ReadWrite)
    GraphicsWinModelBackgrndColor: int = proxy_property('OLE_COLOR','GraphicsWinModelBackgrndColor',AccessMode.ReadWrite)
    HistoryLines: int = proxy_property(int,'HistoryLines',AccessMode.ReadWrite)
    ImageFrameHighlight: bool = proxy_property(bool,'ImageFrameHighlight',AccessMode.ReadWrite)
    LayoutCreateViewport: bool = proxy_property(bool,'LayoutCreateViewport',AccessMode.ReadWrite)
    LayoutCrosshairColor: int = proxy_property('OLE_COLOR','LayoutCrosshairColor',AccessMode.ReadWrite)
    LayoutDisplayMargins: bool = proxy_property(bool,'LayoutDisplayMargins',AccessMode.ReadWrite)
    LayoutDisplayPaper: bool = proxy_property(bool,'LayoutDisplayPaper',AccessMode.ReadWrite)
    LayoutDisplayPaperShadow: bool = proxy_property(bool,'LayoutDisplayPaperShadow',AccessMode.ReadWrite)
    MaxAutoCADWindow: bool = proxy_property(bool,'MaxAutoCADWindow',AccessMode.ReadWrite)
    ModelCrosshairColor: int = proxy_property('OLE_COLOR','ModelCrosshairColor',AccessMode.ReadWrite)
    ShowRasterImage: bool = proxy_property(bool,'ShowRasterImage',AccessMode.ReadWrite)
    TextFont: str = proxy_property(str,'TextFont',AccessMode.ReadWrite)
    TextFontSize: int = proxy_property(int,'TextFontSize',AccessMode.ReadWrite)
    TextFontStyle: AcTextFontStyle = proxy_property('AcTextFontStyle','TextFontStyle',AccessMode.ReadWrite)
    TextWinBackgrndColor: int = proxy_property('OLE_COLOR','TextWinBackgrndColor',AccessMode.ReadWrite)
    TextWinTextColor: int = proxy_property('OLE_COLOR','TextWinBackgrndColor',AccessMode.ReadWrite)
    TrueColorImages: bool = proxy_property(bool,'TrueColorImages',AccessMode.ReadWrite)
    XRefFadeIntensity: int = proxy_property(int,'XRefFadeIntensity',AccessMode.ReadWrite)