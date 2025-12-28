from ..Base import *
from ..Proxy import *
from .AcadUnderlay import AcadUnderlay as AcadUnderlay

class AcadPdfUnderlay(AcadUnderlay):
    def __init__(self, obj) -> None: ...
    def Copy(self) -> AcadPdfUnderlay: ...
