from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesDisplay(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    AutoTrackingVecColor: int
    CursorSize: int
    DisplayLayoutTabs: bool
    DisplayScreenMenu: bool
    DisplayScrollBars: bool
    DockedVisibleLines: int
    GraphicsWinLayoutBackgrndColor: int
    GraphicsWinModelBackgrndColor: int
    HistoryLines: int
    ImageFrameHighlight: bool
    LayoutCreateViewport: bool
    LayoutCrosshairColor: int
    LayoutDisplayMargins: bool
    LayoutDisplayPaper: bool
    LayoutDisplayPaperShadow: bool
    MaxAutoCADWindow: bool
    ModelCrosshairColor: int
    ShowRasterImage: bool
    TextFont: str
    TextFontSize: int
    TextFontStyle: AcTextFontStyle
    TextWinBackgrndColor: int
    TextWinTextColor: int
    TrueColorImages: bool
    XRefFadeIntensity: int
