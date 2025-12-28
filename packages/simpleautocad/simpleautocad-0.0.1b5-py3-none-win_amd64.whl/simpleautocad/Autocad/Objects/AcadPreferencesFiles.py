from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *


    
class AcadPreferencesFiles(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    ActiveInvProject: str = proxy_property(str,'ActiveInvProject',AccessMode.ReadWrite)
    AltFontFile: str = proxy_property(str,'AltFontFile',AccessMode.ReadWrite)
    AltTabletMenuFile: str = proxy_property(str,'AltTabletMenuFile',AccessMode.ReadWrite)
    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    AutoSavePath: str = proxy_property(str,'AutoSavePath',AccessMode.ReadWrite)
    ColorBookPath: str = proxy_property(str,'ColorBookPath',AccessMode.ReadWrite)
    ConfigFile: str = proxy_property(str,'ConfigFile',AccessMode.ReadOnly)
    CustomDictionary: str = proxy_property(str,'CustomDictionary',AccessMode.ReadWrite)
    CustomIconPath: str = proxy_property(str,'CustomIconPath',AccessMode.ReadWrite)
    DefaultInternetURL: str = proxy_property(str,'DefaultInternetURL',AccessMode.ReadWrite)
    DriversPath: str = proxy_property(str,'DriversPath',AccessMode.ReadWrite)
    EnterpriseMenuFile: str = proxy_property(str,'EnterpriseMenuFile',AccessMode.ReadWrite)
    FontFileMap: str = proxy_property(str,'FontFileMap',AccessMode.ReadWrite)
    HelpFilePath: str = proxy_property(str,'HelpFilePath',AccessMode.ReadWrite)
    LogFilePath: str = proxy_property(str,'LogFilePath',AccessMode.ReadWrite)
    MainDictionary: str = proxy_property(str,'MainDictionary',AccessMode.ReadWrite)
    MenuFile: str = proxy_property(str,'MenuFile',AccessMode.ReadWrite)
    PageSetupOverridesTemplateFile: str = proxy_property(str,'PageSetupOverridesTemplateFile',AccessMode.ReadWrite)
    PlotLogFilePath: str = proxy_property(str,'PlotLogFilePath',AccessMode.ReadWrite)
    PostScriptPrologFile: str = proxy_property(str,'PostScriptPrologFile',AccessMode.ReadWrite)
    PrinterConfigPath: str = proxy_property(str,'PrinterConfigPath',AccessMode.ReadWrite)
    PrinterDescPath: str = proxy_property(str,'PrinterDescPath',AccessMode.ReadWrite)
    PrinterStyleSheetPath: str = proxy_property(str,'PrinterStyleSheetPath',AccessMode.ReadWrite)
    PrintFile: str = proxy_property(str,'PrintFile',AccessMode.ReadWrite)
    PrintSpoolerPath: str = proxy_property(str,'PrintSpoolerPath',AccessMode.ReadWrite)
    PrintSpoolExecutable: str = proxy_property(str,'PrintSpoolExecutable',AccessMode.ReadWrite)
    QNewTemplateFile: str = proxy_property(str,'QNewTemplateFile',AccessMode.ReadWrite)
    SupportPath: str = proxy_property(str,'SupportPath',AccessMode.ReadWrite)
    TempFilePath: str = proxy_property(str,'TempFilePath',AccessMode.ReadWrite)
    TemplateDWGPath: str = proxy_property(str,'TemplateDWGPath',AccessMode.ReadWrite)
    TempXRefPath: str = proxy_property(str,'TempXRefPath',AccessMode.ReadWrite)
    TextEditor: str = proxy_property(str,'TextEditor',AccessMode.ReadWrite)
    TextureMapPath: str = proxy_property(str,'TextureMapPath',AccessMode.ReadWrite)
    ToolPalettePath: str = proxy_property(str,'ToolPalettePath',AccessMode.ReadWrite)
    WorkspacePath: str = proxy_property(str,'WorkspacePath',AccessMode.ReadWrite)

    def GetProjectFilePath(self, ProjectName: str) -> Out[str]:
        return self._obj.GetProjectFilePath(ProjectName)
        
    def SetProjectFilePath(self, ProjectName: str, ProjectFilePath: str) -> None:
        self._obj.SetProjectFilePath(ProjectName, ProjectFilePath)