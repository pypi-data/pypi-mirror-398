from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesOpenSave(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    AutoAudit: bool
    AutoSaveInterval: int
    CreateBackup: bool
    DemandLoadARXApp: AcARXDemandLoad
    FullCRCValidation: bool
    IncrementalSavePercent: int
    LogFileOn: bool
    MRUNumber: int
    ProxyImage: AcProxyImage
    SaveAsType: AcSaveAsType
    SavePreviewThumbnail: bool
    ShowProxyDialogBox: bool
    TempFileExtension: str
    XRefDemandLoad: AcXRefDemandLoad
