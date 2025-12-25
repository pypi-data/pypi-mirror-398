from ..Proxy import *
from ..AcadObject import IAcadObjectCollection as IAcadObjectCollection
from .AcadDictionary import AcadDictionary as AcadDictionary

class AcadDictionaries(IAcadObjectCollection):
    def __init__(self, obj) -> None: ...
    def Add(self, Name: str = None) -> AcadDictionary: ...
