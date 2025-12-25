from ..Base import *
from ..Proxy import *
from ...Types.Ac import *
from .AcadApplication import AcadApplication as AcadApplication

class AcadSecurityParams(AppObject):
    def __init__(self, obj) -> None: ...
    Action: AcadSecurityParamsType
    Algorithm: AcadSecurityParamsConstants
    Comment: str
    Issuer: str
    KeyLength: int
    Password: str
    ProviderName: str
    ProviderType: int
    SerialNumber: str
    Subject: str
    TimeServer: str
