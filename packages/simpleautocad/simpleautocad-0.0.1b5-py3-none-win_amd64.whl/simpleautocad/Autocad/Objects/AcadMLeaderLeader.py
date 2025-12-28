from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *
from .AcadSubEntity import *

class AcadMLeaderLeader(AcadSubEntity):
    def __init__(self, obj) -> None: super().__init__(obj)
    
    ArrowheadBlock: str = proxy_property(str,'ArrowheadBlock',AccessMode.ReadWrite)
    ArrowheadSize: int = proxy_property(int,'ArrowheadSize',AccessMode.ReadWrite)
    ArrowheadType: AcDimArrowheadType = proxy_property('AcDimArrowheadType','ArrowheadType',AccessMode.ReadWrite)
    LeaderLineColor: AcadAcCmColor = proxy_property('AcadAcCmColor','LeaderLineColor',AccessMode.ReadWrite)
    LeaderLinetype: str = proxy_property(str,'LeaderLinetype',AccessMode.ReadWrite)
    LeaderLineWeight: AcLineWeight = proxy_property('AcLineWeight','LeaderLineWeight',AccessMode.ReadWrite)
    LeaderType: AcMLeaderType = proxy_property('AcMLeaderType','LeaderType',AccessMode.ReadWrite)
