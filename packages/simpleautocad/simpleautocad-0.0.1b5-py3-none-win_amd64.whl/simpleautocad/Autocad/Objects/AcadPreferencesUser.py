from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesUser(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    ADCInsertUnitsDefaultSource: AcInsertUnits = proxy_property('AcInsertUnits','ADCInsertUnitsDefaultSource',AccessMode.ReadWrite)
    ADCInsertUnitsDefaultTarget: AcInsertUnits = proxy_property('AcInsertUnits','ADCInsertUnitsDefaultTarget',AccessMode.ReadWrite)
    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    HyperlinkDisplayCursor: bool = proxy_property(bool,'HyperlinkDisplayCursor',AccessMode.ReadWrite)
    KeyboardAccelerator: AcKeyboardAccelerator = proxy_property('AcKeyboardAccelerator','KeyboardAccelerator',AccessMode.ReadWrite)
    KeyboardPriority: AcKeyboardPriority = proxy_property('AcKeyboardPriority','KeyboardPriority',AccessMode.ReadWrite)
    SCMCommandMode: AcDrawingAreaSCMCommand = proxy_property('AcDrawingAreaSCMCommand','SCMCommandMode',AccessMode.ReadWrite)
    SCMDefaultMode: AcDrawingAreaSCMDefault = proxy_property('AcDrawingAreaSCMDefault','SCMDefaultMode',AccessMode.ReadWrite)
    SCMEditMode: AcDrawingAreaSCMEdit = proxy_property('AcDrawingAreaSCMEdit','SCMEditMode',AccessMode.ReadWrite)
    SCMTimeMode: bool = proxy_property(bool,'SCMTimeMode',AccessMode.ReadWrite)
    SCMTimeValue: int = proxy_property(int,'SCMTimeValue',AccessMode.ReadWrite)
    ShortCutMenuDisplay: bool = proxy_property(bool,'ShortCutMenuDisplay',AccessMode.ReadWrite)
