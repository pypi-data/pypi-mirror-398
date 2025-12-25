from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadHyperlink(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    URL: str
    URLDescription: str
    URLNamedLocation: str
    def Delete(self) -> None: ...
