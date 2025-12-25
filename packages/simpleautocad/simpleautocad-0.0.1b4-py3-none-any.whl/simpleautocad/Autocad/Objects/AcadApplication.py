from __future__ import annotations
from ..Base import *
from ..AcadObject import *
from ..Proxy import *
from .AcadState import AcadState


class AcadApplication(Application, AppObject):
    _first_instance_initialized = False
    __app_name__ = 'AutoCAD'
    __app_version__ = None

    @staticmethod
    def set_version(version:str):
        if AcadApplication.__app_version__ is None:
            AcadApplication.__app_version__ = version

    def _manage_application_instance(self) -> CDispatch:
        if not AcadApplication._first_instance_initialized:
            clsid = get_clsid(self)
            AcadApplication.__app_clsid__ = clsid[0]
            AcadApplication.__app_full_name__ = clsid[1]
            acad_app = com_server_is_running(AcadApplication.__app_full_name__)
            self._is_owner = not bool(acad_app)
            if not acad_app:
                acad_app = AppCreate(AcadApplication.__app_full_name__)
        else:
            acad_app = create_new_instance_explicitly(AcadApplication.__app_full_name__)
            self._is_owner = True
        AcadApplication._first_instance_initialized = True
        return acad_app

    ActiveDocument: AcadDocument = proxy_property('AcadDocument','ActiveDocument',AccessMode.ReadOnly)
    Application: 'AcadApplication' = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Caption: str = proxy_property(str,'Caption', AccessMode.ReadOnly)
    Documents: AcadDocuments = proxy_property('AcadDocuments','Documents',AccessMode.ReadOnly)
    FullName: str = proxy_property(str,'FullName',AccessMode.ReadOnly)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    HWND: int = proxy_property(int,'HWND',AccessMode.ReadOnly)
    LocaleId: int = proxy_property(int,'LocaleId',AccessMode.ReadOnly)
    MenuBar: AcadMenuBar = proxy_property('AcadMenuBar','MenuBar',AccessMode.ReadOnly)
    MenuGroups: AcadMenuGroups = proxy_property('AcadMenuGroups','MenuGroups',AccessMode.ReadOnly)
    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)
    Path: str = proxy_property(str,'Path',AccessMode.ReadOnly)
    Preferences: AcadPreferences = proxy_property('AcadPreferences','Preferences',AccessMode.ReadOnly)
    VBE: AppObject = proxy_property('AppObject','VBE',AccessMode.ReadOnly)
    Version: str = proxy_property(str,'Version',AccessMode.ReadOnly)
    Visible: bool = proxy_property(bool,'Visible',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)
    WindowLeft: int = proxy_property(int,'WindowLeft',AccessMode.ReadWrite)
    WindowState: int = proxy_property(int,'WindowState',AccessMode.ReadWrite)
    WindowTop: int = proxy_property(int,'WindowTop',AccessMode.ReadWrite)

    def StatusID(self, VportObj: AcadViewport) -> bool: 
        return self._obj.StatusId(VportObj())

    def Eval(self, Expression: str) -> None: 
        self._obj.Eval(Expression)

    def GetAcadState(self) -> AcadState: 
        return AcadState(self._obj.GetAcadState())

    def GetInterfaceObject(self, ProgID: str) -> AppObject: 
        return AppObject(self._obj.GetInterfaceObject(ProgID))

    def ListARX(self) -> vStringArray: 
        return vStringArray(self._obj.ListArx())

    def LoadARX(self, Name) -> None: 
        self._obj.LoadArx(Name)

    def LoadDVB(self, Name) -> None: 
        self._obj.LoadDVB(Name)

    def Quit(self) -> None: 
        self._obj.Quit()

    def RunMacro(self, MacroPath: str) -> None: 
        self._obj.RunMacro(MacroPath)

    def UnloadARX(self, Name: str) -> None:
        self._obj.UnloadArx(Name)

    def UnloadDVB(self, Name: str) -> None: 
        self._obj.UnloadDVB(Name)

    def Update(self) -> None: 
        self._obj.Update()

    def ZoomAll(self) -> None: 
        self._obj.ZoomAll()

    def ZoomCenter(self, Center: PyGePoint3d, Magnify: float) -> None: 
        self._obj.ZoomCenter(Center(), Magnify)

    def ZoomExtents(self) -> None: 
        self._obj.ZoomExtents()

    def ZoomPickWindow(self) -> None: 
        self._obj.ZoomPickWindow()

    def ZoomPrevious(self) -> None: 
        self._obj.ZoomPrevious()

    def ZoomScaled(self, Scale: float, ScaleType: AcZoomScaleType) -> None: 
        self._obj.ZoomScaled(Scale, ScaleType)

    def ZoomWindow(self, LowerLeft: PyGePoint3d, UpperRight: PyGePoint3d) -> None: 
        self._obj.ZoomWindow(LowerLeft(), UpperRight())