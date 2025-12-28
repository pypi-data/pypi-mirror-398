from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesUser(AppObject):
    def __init__(self, obj) -> None: ...
    ADCInsertUnitsDefaultSource: AcInsertUnits
    ADCInsertUnitsDefaultTarget: AcInsertUnits
    Application: AcadApplication
    HyperlinkDisplayCursor: bool
    KeyboardAccelerator: AcKeyboardAccelerator
    KeyboardPriority: AcKeyboardPriority
    SCMCommandMode: AcDrawingAreaSCMCommand
    SCMDefaultMode: AcDrawingAreaSCMDefault
    SCMEditMode: AcDrawingAreaSCMEdit
    SCMTimeMode: bool
    SCMTimeValue: int
    ShortCutMenuDisplay: bool
