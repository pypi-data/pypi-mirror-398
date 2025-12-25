from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *

        
        
class AcadPreferencesOpenSave(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    AutoAudit: bool = proxy_property(bool,'AutoAudit',AccessMode.ReadWrite)
    AutoSaveInterval: int = proxy_property(int,'AutoSaveInterval',AccessMode.ReadWrite)
    CreateBackup: bool = proxy_property(bool,'CreateBackup',AccessMode.ReadWrite)
    DemandLoadARXApp: AcARXDemandLoad  = proxy_property('AcARXDemandLoad','DemandLoadARXApp',AccessMode.ReadWrite)
    FullCRCValidation: bool  = proxy_property(bool,'FullCRCValidation',AccessMode.ReadWrite)
    IncrementalSavePercent: int  = proxy_property(int,'IncrementalSavePercent',AccessMode.ReadWrite)
    LogFileOn: bool  = proxy_property(bool,'LogFileOn',AccessMode.ReadWrite)
    MRUNumber: int  = proxy_property(int,'MRUNumber',AccessMode.ReadOnly)
    ProxyImage: AcProxyImage = proxy_property('AcProxyImage','ProxyImage',AccessMode.ReadWrite)
    SaveAsType: AcSaveAsType  = proxy_property('AcSaveAsType','SaveAsType',AccessMode.ReadWrite)
    SavePreviewThumbnail: bool  = proxy_property(bool,'SavePreviewThumbnail',AccessMode.ReadWrite)
    ShowProxyDialogBox: bool  = proxy_property(bool,'ShowProxyDialogBox',AccessMode.ReadWrite)
    TempFileExtension: str  = proxy_property(str,'TempFileExtension',AccessMode.ReadWrite)
    XRefDemandLoad: AcXRefDemandLoad = proxy_property('AcXRefDemandLoad','XRefDemandLoad',AccessMode.ReadWrite)