from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferencesSelection(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    DisplayGrips: bool
    DisplayGripsWithinBlocks: bool
    GripColorSelected: AcColor
    GripColorUnselected: AcColor
    GripSize: int
    PickAdd: bool
    PickAuto: bool
    PickBoxSize: int
    PickDrag: bool
    PickFirst: bool
    PickGroup: bool
