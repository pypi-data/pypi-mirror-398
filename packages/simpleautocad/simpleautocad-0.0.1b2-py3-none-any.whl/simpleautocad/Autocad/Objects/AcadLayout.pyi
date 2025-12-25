from ..Base import *
from ..Proxy import *
from .AcadPlotConfiguration import *

class AcadLayout(AcadPlotConfiguration):
    def __init__(self, obj) -> None: ...
    Block: AcadBlock
    TabOrder: int
