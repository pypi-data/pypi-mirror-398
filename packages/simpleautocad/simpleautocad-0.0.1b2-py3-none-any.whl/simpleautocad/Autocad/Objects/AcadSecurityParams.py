from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadApplication import AcadApplication
from ...Types.Ac import *



class AcadSecurityParams(AppObject):
    def __init__(self, obj) -> None: 
        super().__init__(obj)

    Action: AcadSecurityParamsType = proxy_property('AcadSecurityParamsType','Action',AccessMode.ReadWrite)
    Algorithm: AcadSecurityParamsConstants = proxy_property('AcadSecurityParamsConstants','Algorithm',AccessMode.ReadWrite)
    Comment: str = proxy_property(str,'Comment',AccessMode.ReadWrite)
    Issuer: str = proxy_property(str,'Issuer',AccessMode.ReadWrite)
    KeyLength: int = proxy_property(int,'KeyLength',AccessMode.ReadWrite)
    Password: str = proxy_property(str,'Password',AccessMode.ReadWrite)
    ProviderName: str = proxy_property(str,'ProviderName',AccessMode.ReadWrite)
    ProviderType: int = proxy_property(int,'ProviderType',AccessMode.ReadWrite)
    SerialNumber: str = proxy_property(str,'SerialNumber',AccessMode.ReadWrite)
    Subject: str = proxy_property(str,'Subject',AccessMode.ReadWrite)
    TimeServer: str = proxy_property(str,'TimeServer',AccessMode.ReadWrite)
