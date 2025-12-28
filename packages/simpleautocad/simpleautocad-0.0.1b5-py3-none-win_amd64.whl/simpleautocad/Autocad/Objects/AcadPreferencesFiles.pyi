from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesFiles(AppObject):
    def __init__(self, obj) -> None: ...
    ActiveInvProject: str
    AltFontFile: str
    AltTabletMenuFile: str
    Application: AcadApplication
    AutoSavePath: str
    ColorBookPath: str
    ConfigFile: str
    CustomDictionary: str
    CustomIconPath: str
    DefaultInternetURL: str
    DriversPath: str
    EnterpriseMenuFile: str
    FontFileMap: str
    HelpFilePath: str
    LogFilePath: str
    MainDictionary: str
    MenuFile: str
    PageSetupOverridesTemplateFile: str
    PlotLogFilePath: str
    PostScriptPrologFile: str
    PrinterConfigPath: str
    PrinterDescPath: str
    PrinterStyleSheetPath: str
    PrintFile: str
    PrintSpoolerPath: str
    PrintSpoolExecutable: str
    QNewTemplateFile: str
    SupportPath: str
    TempFilePath: str
    TemplateDWGPath: str
    TempXRefPath: str
    TextEditor: str
    TextureMapPath: str
    ToolPalettePath: str
    WorkspacePath: str
    def GetProjectFilePath(self, ProjectName: str) -> Out[str]: ...
    def SetProjectFilePath(self, ProjectName: str, ProjectFilePath: str) -> None: ...
