from ..Base import *
from ..AcadObject import *
from .AcadSubEntity import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadMLeaderLeader(AcadSubEntity):
    def __init__(self, obj) -> None: ...
    ArrowheadBlock: str
    ArrowheadSize: int
    ArrowheadType: AcDimArrowheadType
    LeaderLineColor: AcadAcCmColor
    LeaderLinetype: str
    LeaderLineWeight: AcLineWeight
    LeaderType: AcMLeaderType
