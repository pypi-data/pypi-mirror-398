from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadPlotConfiguration import *



class AcadLayout(AcadPlotConfiguration):
    def __init__(self, obj) -> None: super().__init__(obj)

    Block: AcadBlock = proxy_property('AcadBlock','Block',AccessMode.ReadOnly)
    TabOrder: int = proxy_property(int,'TabOrder',AccessMode.ReadWrite)
