from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadPreferencesSelection(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    DisplayGrips: bool = proxy_property(bool,'DisplayGrips',AccessMode.ReadWrite)
    DisplayGripsWithinBlocks: bool = proxy_property(bool,'DisplayGripsWithinBlocks',AccessMode.ReadWrite)
    GripColorSelected: AcColor = proxy_property('AcColor','GripColorSelected',AccessMode.ReadWrite)
    GripColorUnselected: AcColor = proxy_property('AcColor','GripColorUnselected',AccessMode.ReadWrite)
    GripSize: int = proxy_property(int,'GripSize',AccessMode.ReadWrite)
    PickAdd: bool = proxy_property(bool,'PickAdd',AccessMode.ReadWrite)
    PickAuto: bool = proxy_property(bool,'PickAuto',AccessMode.ReadWrite)
    PickBoxSize: int = proxy_property(int,'PickBoxSize',AccessMode.ReadWrite)
    PickDrag: bool = proxy_property(bool,'PickDrag',AccessMode.ReadWrite)
    PickFirst: bool = proxy_property(bool,'PickFirst',AccessMode.ReadWrite)
    PickGroup: bool = proxy_property(bool,'PickGroup',AccessMode.ReadWrite)