from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadXRecord(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    TranslateIDs: bool = proxy_property(bool,'TranslateIDs',AccessMode.ReadWrite)

    def GetXRecordData(self) -> tuple: 
        XRecordDataType, XRecordDataValue = self._obj.GetXRecordData()
        return XRecordDataType, XRecordDataValue

    def SetXRecordData(self, XRecordDataType: Variant, XRecordData: Variant) -> None: 
        self._obj.SetXRecordData(XRecordDataType(), XRecordData())
