from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadState(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    IsQuiescent: bool
