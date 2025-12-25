from ..Base import *
from ..Proxy import *
from .AcadBlockReference import AcadBlockReference as AcadBlockReference

class AcadMInsertBlock(AcadBlockReference):
    def __init__(self, obj) -> None: ...
    Columns: int
    ColumnSpacing: float
    def Copy(self) -> AcadMInsertBlock: ...
