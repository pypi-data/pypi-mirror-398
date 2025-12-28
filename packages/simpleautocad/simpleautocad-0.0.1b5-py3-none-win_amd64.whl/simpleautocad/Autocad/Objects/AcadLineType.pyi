from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadLineType(AcadObject):
    def __init__(self, obj) -> None: ...
    Description: str
    Name: str
