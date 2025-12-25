from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadHelix(AcadEntity):
    def __init__(self, obj) -> None: ...
    BaseRadius: float
    Constrain: AcHelixConstrainType
    Height: float
    Position: PyGePoint3d
    TopRadius: float
    TotalLength: float
    TurnHeight: float
    Turns: int
    TurnSlope: float
    Twist: AcHelixTwistType
    def Copy(self) -> AcadHelix: ...
