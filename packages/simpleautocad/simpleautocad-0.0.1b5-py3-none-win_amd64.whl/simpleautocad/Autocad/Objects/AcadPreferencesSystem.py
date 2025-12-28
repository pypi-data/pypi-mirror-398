from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesSystem(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    BeepOnError: bool = proxy_property(bool,'BeepOnError',AccessMode.ReadWrite)
    DisplayOLEScale: bool = proxy_property(bool,'DisplayOLEScale',AccessMode.ReadWrite)
    EnableStartupDialog: bool = proxy_property(bool,'EnableStartupDialog',AccessMode.ReadWrite)
    LoadAcadLspInAllDocuments: bool = proxy_property(bool,'LoadAcadLspInAllDocuments',AccessMode.ReadWrite)
    ShowWarningMessages: bool = proxy_property(bool,'ShowWarningMessages',AccessMode.ReadWrite)
    SingleDocumentMode: bool = proxy_property(bool,'SingleDocumentMode',AccessMode.ReadWrite)
    StoreSQLIndex: bool = proxy_property(bool,'StoreSQLIndex',AccessMode.ReadWrite)
    TablesReadOnly: bool = proxy_property(bool,'TablesReadOnly',AccessMode.ReadWrite)