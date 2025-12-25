from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadTableStyle(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)
    
    BitFlags: int = proxy_property(int,'BitFlags',AccessMode.ReadWrite)
    Description: str = proxy_property(str,'Description',AccessMode.ReadWrite)
    FlowDirection: AcTableDirection = proxy_property('AcTableDirection','FlowDirection',AccessMode.ReadWrite)
    HeaderSuppressed: bool = proxy_property(bool,'HeaderSuppressed',AccessMode.ReadWrite)
    HorzCellMargin: float = proxy_property(float,'HorzCellMargin',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    NumCellStyles: int = proxy_property(int,'NumCellStyles',AccessMode.ReadOnly)
    TemplateId: int = proxy_property(int,'TemplateId',AccessMode.ReadWrite)
    TitleSuppressed: bool = proxy_property(bool,'TitleSuppressed',AccessMode.ReadWrite)
    VertCellMargin: float = proxy_property(float,'VertCellMargin',AccessMode.ReadWrite)

    def CreateCellStyle(self, StringCellStyle: str) -> None:
        self._obj.CreateCellStyle(StringCellStyle)

    def CreateCellStyleFromStyle(self, StringCellStyle: str, StringSourceCellStyle: str) -> None:
        self._obj.CreateCellStyleFromStyle(StringCellStyle, StringSourceCellStyle)

    def DeleteCellStyle(self, StringCellStyle: str) -> None:
        self._obj.DeleteCellStyle(StringCellStyle)

    def EnableMergeAll(self, nRow: int, nCol: int, bEnable: bool) -> None:
        self._obj.EnableMergeAll(nRow, nCol, bEnable)

    def GetAlignment(self, rowType: AcRowType) -> AcCellAlignment:
        return AcCellAlignment(self._obj.GetAlignment(rowType))

    def GetAlignment2(self, bstrCellStyle: str) -> AcCellAlignment:
        return AcCellAlignment(self._obj.GetAlignment2(bstrCellStyle))

    def GetBackgroundColor(self, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetBackgroundColor(rowType))

    def GetBackgroundColor2(self, bstrCellStyle: str) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetBackgroundColor2(bstrCellStyle))

    def GetBackgroundColorNone(self, rowType: AcRowType) -> bool:
        return self._obj.GetBackgroundColorNone(rowType)

    def GetCellClass(self, StringCellStyle: str) -> int:
        return self._obj.GetCellClass(StringCellStyle)

    def GetCellStyles(self) -> Variant:
        cellStylesArray = self._obj.GetCellStyles()
        return Variant(cellStylesArray)

    def GetColor(self, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetColor(rowType))

    def GetColor2(self, bstrCellStyle: str) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetColor2(bstrCellStyle))

    def GetDataType(self, rowType: AcRowType) -> tuple:
        pDataType, pUnitType = self._obj.GetDataType(rowType)
        return AcValueDataType(pDataType), AcValueUnitType(pUnitType)

    def GetDataType2(self, nRow: int, nCol: int, nContent: int) -> tuple:
        pDataType, pUnitType = self._obj.GetDataType2(nRow, nCol, nContent)
        return AcValueDataType(pDataType), AcValueUnitType(pUnitType)

    def GetFormat(self, rowType: AcRowType) -> str:
        return self._obj.GetFormat(rowType)

    def GetFormat2(self, StringCellStyle: str) -> str:
        pbstrFormat = self._obj.GetFormat2(StringCellStyle)
        return pbstrFormat

    def GetGridColor(self, gridLineType: AcGridLineType, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetGridColor(gridLineType, rowType))

    def GetGridColor2(self, bstrCellStyle: str, gridLineType: AcGridLineType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetGridColor2(bstrCellStyle, gridLineType))

    def GetGridLineWeight(self, gridLineType: AcGridLineType, rowType: AcRowType) -> AcLineWeight:
        return AcLineWeight(self._obj.GetGridLineWeight(gridLineType, rowType))

    def GetGridLineWeight2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> AcLineWeight:
        return AcLineWeight(self._obj.GetGridLineWeight2(nRow, nCol, nGridLineType))

    def GetGridVisibility(self, gridLineType: AcGridLineType, rowType: AcRowType) -> bool:
        return self._obj.GetGridVisibility(gridLineType, rowType)

    def GetGridVisibility2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> bool:
        return self._obj.GetGridVisibility2(nRow, nCol, nGridLineType)

    def GetIsCellStyleInUse(self, pszCellStyle: str) -> bool:
        return self._obj.GetIsCellStyleInUse(pszCellStyle)

    def GetIsMergeAllEnabled(self, StringCellStyle: str) -> bool:
        return self._obj.GetIsMergeAllEnabled(StringCellStyle)

    def GetRotation(self, StringCellStyle: str) -> float:
        return self._obj.GetRotation(StringCellStyle)

    def GetTextHeight(self, rowType: AcRowType) -> float:
        return self._obj.GetTextHeight(rowType)

    def GetTextHeight2(self, StringCellStyle: str) -> float:
        return self._obj.GetTextHeight2(StringCellStyle)

    def GetTextStyle(self, rowType: AcRowType) -> str:
        return self._obj.GetTextStyle(rowType)

    def GetTextStyleId(self, bstrCellStyle: str) -> float:
        return self._obj.GetTextStyleId(bstrCellStyle)

    def GetUniqueCellStyleName(self, pszBaseName: str) -> str:
        return self._obj.GetUniqueCellStyleName(pszBaseName)

    def RenameCellStyle(self, StringOldName: str, StringNewName: str) -> None:
        self._obj.RenameCellStyle(StringOldName, StringNewName)

    def SetAlignment(self, rowTypes: AcRowType, cellAlignment: AcCellAlignment) -> None:
        self._obj.SetAlignment(rowTypes, cellAlignment)

    def SetAlignment2(self, bstrCellStyle: str, cellAlignment: AcCellAlignment) -> None:
        self._obj.SetAlignment2(bstrCellStyle, cellAlignment)

    def SetBackgroundColor(self, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetBackgroundColor(rowTypes, pColor())

    def SetBackgroundColor2(self, bstrCellStyle: str, color: AcadAcCmColor) -> None:
        self._obj.SetBackgroundColor2(bstrCellStyle, color())

    def SetBackgroundColorNone(self, rowTypes: AcRowType, bValue: bool) -> None:
        self._obj.SetBackgroundColorNone(rowTypes, bValue)

    def SetCellClass(self, StringCellStyle: str, cellClass: int) -> None:
        self._obj.SetCellClass(StringCellStyle, cellClass)

    def SetColor(self, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetColor(rowTypes, pColor())

    def SetColor2(self, bstrCellStyle: str, color: AcadAcCmColor) -> None:
        self._obj.SetColor2(bstrCellStyle, color())

    def SetDataType(self, rowTypes: AcRowType, nDataType: AcValueDataType, nUnitType: AcValueUnitType) -> None:
        self._obj.SetDataType(rowTypes, nDataType, nUnitType)

    def SetDataType2(self, nRow: int, nCol: int, nContent: int, dataType: AcValueDataType, unitType: AcValueUnitType) -> None:
        self._obj.SetDataType2(nRow, nCol, nContent, dataType, unitType)

    def SetFormat(self, rowTypes: AcRowType, pFormat: str) -> None:
        self._obj.SetFormat(rowTypes, pFormat)

    def SetFormat2(self, bstrCellStyle: str, bstrFormat: str) -> None:
        self._obj.SetFormat2(bstrCellStyle, bstrFormat)

    def SetGridColor(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetGridColor(gridLineTypes, rowTypes, pColor())

    def SetGridColor2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, pColor: AcadAcCmColor) -> None:
        self._obj.SetGridColor2(nRow, nCol, nGridLineType, pColor())

    def SetGridLineWeight(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, Lineweight: AcLineWeight) -> None:
        self._obj.SetGridLineWeight(gridLineTypes, rowTypes, Lineweight)

    def SetGridLineWeight2(self, bstrCellStyle: str, gridLineType: AcGridLineType, Lineweight: AcLineWeight) -> None:
        self._obj.SetGridLineWeight2(bstrCellStyle, gridLineType, Lineweight)

    def SetGridVisibility(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, bVisible: bool) -> None:
        self._obj.SetGridVisibility(gridLineTypes, rowTypes, bVisible)

    def SetGridVisibility2(self, bstrCellStyle: str, gridLineType: AcGridLineType, bValue: bool) -> None:
        self._obj.SetGridVisibility2(bstrCellStyle, gridLineType, bValue)

    def SetRotation(self, bstrCellStyle: str, Rotation: float) -> None:
        self._obj.SetRotation(bstrCellStyle, Rotation)

    def SetTemplateId(self, val: int, option: AcMergeCellStyleOption) -> None:
        self._obj.SetTemplateId(val, option)

    def SetTextHeight(self, rowTypes: AcRowType, TextHeight: float) -> None:
        self._obj.SetTextHeight(rowTypes, TextHeight)

    def SetTextHeight2(self, bstrCellStyle: str, Height: float) -> None:
        self._obj.SetTextHeight2(bstrCellStyle, Height)

    def SetTextStyle(self, rowTypes: AcRowType, bstrName: str) -> None:
        self._obj.SetTextStyle(rowTypes, bstrName)

    def SetTextStyleId(self, bstrCellStyle: str, val: int) -> None:
        self._obj.SetTextStyleId(bstrCellStyle, val)