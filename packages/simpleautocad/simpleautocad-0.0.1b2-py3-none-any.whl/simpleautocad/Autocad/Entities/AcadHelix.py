from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadHelix(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    BaseRadius: float = proxy_property(float,'BaseRadius',AccessMode.ReadWrite)
    Constrain: AcHelixConstrainType = proxy_property('AcHelixConstrainType','Constrain',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    Position: PyGePoint3d = proxy_property('PyGePoint3d','Position',AccessMode.ReadWrite)
    TopRadius: float = proxy_property(float,'TopRadius',AccessMode.ReadWrite)
    TotalLength: float = proxy_property(float,'TotalLength',AccessMode.ReadWrite)
    TurnHeight: float = proxy_property(float,'TurnHeight',AccessMode.ReadWrite)
    Turns: int = proxy_property(int,'Turns',AccessMode.ReadWrite)
    TurnSlope: float = proxy_property(float,'TurnSlope',AccessMode.ReadWrite)
    Twist: AcHelixTwistType = proxy_property('AcHelixTwistType','Twist',AccessMode.ReadWrite)

    def Copy(self) -> AcadHelix:
        return AcadHelix(self._obj.Copy())