from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadIDPair(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    IsCloned: bool
    IsOwnerXlated: bool
    IsPrimary: bool
    Key: int
