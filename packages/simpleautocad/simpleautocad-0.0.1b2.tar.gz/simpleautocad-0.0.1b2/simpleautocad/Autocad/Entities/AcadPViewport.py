from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPViewport(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    ArcSmoothness: int = proxy_property(int,'ArcSmoothness',AccessMode.ReadWrite)
    Center: PyGePoint3d = proxy_property('PyGePoint3d','Center',AccessMode.ReadWrite)
    Clipped: bool = proxy_property(bool,'Clipped',AccessMode.ReadOnly)
    CustomScale: float = proxy_property(float,'CustomScale',AccessMode.ReadWrite)
    Direction: PyGeVector3d = proxy_property('PyGeVector3d','Direction',AccessMode.ReadWrite)
    DisplayLocked: bool = proxy_property(bool,'DisplayLocked',AccessMode.ReadWrite)
    DisplayLocked: bool = proxy_property(bool,'DisplayLocked',AccessMode.ReadWrite)
    GridOn: bool = proxy_property(bool,'GridOn',AccessMode.ReadWrite)
    HasSheetView: bool = proxy_property(bool,'HasSheetView',AccessMode.ReadOnly)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    LabelBlockId: int = proxy_property(int,'LabelBlockId',AccessMode.ReadWrite)
    LayerPropertyOverrides: bool = proxy_property(bool,'LayerPropertyOverrides',AccessMode.ReadOnly)
    LensLength: float = proxy_property(float,'LensLength',AccessMode.ReadWrite)
    ModelView: AcadView = proxy_property('AcadView','ModelView',AccessMode.ReadWrite)
    ShadePlot: AcShadePlot = proxy_property('AcShadePlot','ShadePlot',AccessMode.ReadWrite)
    SheetView: AcadView = proxy_property('AcadView','SheetView',AccessMode.ReadWrite)
    SnapBasePoint: PyGePoint2d = proxy_property('PyGePoint2d','SnapBasePoint',AccessMode.ReadWrite)
    SnapOn: bool = proxy_property(bool,'SnapOn',AccessMode.ReadWrite)
    SnapRotationAngle: float = proxy_property(float,'SnapRotationAngle',AccessMode.ReadWrite)
    StandardScale: AcViewportScale = proxy_property('AcViewportScale','StandardScale',AccessMode.ReadWrite)
    StandardScale2: int = proxy_property(int,'StandardScale2',AccessMode.ReadWrite)
    Target: PyGePoint3d = proxy_property('PyGePoint3d','Target',AccessMode.ReadWrite)
    TwistAngle: float = proxy_property(float,'TwistAngle',AccessMode.ReadWrite)
    UCSIconAtOrigin: bool = proxy_property(bool,'UCSIconAtOrigin',AccessMode.ReadWrite)
    UCSIconOn: bool = proxy_property(bool,'UCSIconOn',AccessMode.ReadWrite)
    UCSPerViewport: bool = proxy_property(bool,'UCSPerViewport',AccessMode.ReadWrite)
    ViewportOn: bool = proxy_property(bool,'ViewportOn',AccessMode.ReadWrite)
    VisualStyle: int = proxy_property(int,'VisualStyle',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def Copy(self) -> AcadPViewport:
        return AcadPViewport(self._obj.Copy())
        
    def GetGridSpacing(self) -> tuple:
        XSpacing, YSpacing = self._obj.GetGridSpacing()
        return XSpacing, YSpacing
        
    def GetSnapSpacing(self) -> tuple:
        XSpacing, YSpacing = self._obj.GetSnapSpacing()
        return XSpacing, YSpacing
        
    def SetGridSpacing(self, XSpacing: float, YSpacing: float) -> None:
        self._obj.SetGridSpacing(XSpacing, YSpacing)
        
    def SetSnapSpacing(self, XSpacing: float, YSpacing: float) -> None:
        self._obj.SetSnapSpacing(XSpacing, YSpacing)
        
    def SyncModelView(self) -> None:
        self._obj.SyncModelView()
