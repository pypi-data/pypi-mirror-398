from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadSectionSettings(AcadObject):
    def __init__(self, obj) -> None: ...
    CurrentSectionType: AcSectionType
