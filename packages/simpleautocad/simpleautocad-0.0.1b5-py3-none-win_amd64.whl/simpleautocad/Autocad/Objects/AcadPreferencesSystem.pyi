from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesSystem(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    BeepOnError: bool
    DisplayOLEScale: bool
    EnableStartupDialog: bool
    LoadAcadLspInAllDocuments: bool
    ShowWarningMessages: bool
    SingleDocumentMode: bool
    StoreSQLIndex: bool
    TablesReadOnly: bool
