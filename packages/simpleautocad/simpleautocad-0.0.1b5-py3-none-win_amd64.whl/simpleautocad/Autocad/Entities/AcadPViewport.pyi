from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadPViewport(AcadEntity):
    def __init__(self, obj) -> None: ...
    ArcSmoothness: int
    Center: PyGePoint3d
    Clipped: bool
    CustomScale: float
    Direction: PyGeVector3d
    DisplayLocked: bool
    GridOn: bool
    HasSheetView: bool
    Height: float
    LabelBlockId: int
    LayerPropertyOverrides: bool
    LensLength: float
    ModelView: AcadView
    ShadePlot: AcShadePlot
    SheetView: AcadView
    SnapBasePoint: PyGePoint2d
    SnapOn: bool
    SnapRotationAngle: float
    StandardScale: AcViewportScale
    StandardScale2: int
    Target: PyGePoint3d
    TwistAngle: float
    UCSIconAtOrigin: bool
    UCSIconOn: bool
    UCSPerViewport: bool
    ViewportOn: bool
    VisualStyle: int
    Width: float
    def Copy(self) -> AcadPViewport: ...
    def GetGridSpacing(self) -> tuple: ...
    def GetSnapSpacing(self) -> tuple: ...
    def SetGridSpacing(self, XSpacing: float, YSpacing: float) -> None: ...
    def SetSnapSpacing(self, XSpacing: float, YSpacing: float) -> None: ...
    def SyncModelView(self) -> None: ...
