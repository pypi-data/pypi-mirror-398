from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadMenuGroup(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: 'AcadApplication' = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    MenuFileName: str = proxy_property(str,'MenuFileName',AccessMode.ReadOnly)
    Menus: AcadPopupMenus = proxy_property('AcadPopupMenus','Menus',AccessMode.ReadOnly)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)
    Toolbars: AcadToolbars = proxy_property('AcadToolbars','Toolbars',AccessMode.ReadOnly)
    Type: AcMenuGroupType  = proxy_property('AcMenuGroupType','Type',AccessMode.ReadOnly)

    def Save(self, MenuFileType: AcMenuFileType) -> None: 
        self._obj.Save(MenuFileType)

    def SaveAs(self, MenuFileName: str, MenuFileType: AcMenuFileType) -> None: 
        self._obj.SaveAs(MenuFileName, MenuFileType)
        
    def Unload(self) -> None: 
        self._obj.Unload()