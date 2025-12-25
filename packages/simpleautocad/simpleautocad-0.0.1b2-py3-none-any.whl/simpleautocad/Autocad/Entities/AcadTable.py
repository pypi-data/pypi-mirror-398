from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadTable(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    AllowManualHeights: bool = proxy_property(bool,'AllowManualHeights',AccessMode.ReadWrite)
    AllowManualPositions: bool = proxy_property(bool,'AllowManualPositions',AccessMode.ReadWrite)
    BreaksEnabled: bool = proxy_property(bool,'BreaksEnabled',AccessMode.ReadWrite)
    BreakSpacing: float = proxy_property(float,'BreakSpacing',AccessMode.ReadWrite)
    Columns: int = proxy_property(int,'Columns',AccessMode.ReadWrite)
    ColumnWidth: float = proxy_property(float,'ColumnWidth',AccessMode.ReadWrite)
    Direction: PyGeVector3d = proxy_property(PyGeVector3d,'Direction',AccessMode.ReadWrite)
    EnableBreak: bool = proxy_property(bool,'EnableBreak',AccessMode.ReadWrite)
    FlowDirection: AcTableDirection = proxy_property('AcTableDirection','FlowDirection',AccessMode.ReadWrite)
    HasSubSelection: bool = proxy_property(bool,'HasSubSelection',AccessMode.ReadWrite)
    HeaderSuppressed: bool = proxy_property(bool,'HeaderSuppressed',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    HorzCellMargin: float = proxy_property(float,'HorzCellMargin',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    MinimumTableHeight: float = proxy_property(float,'MinimumTableHeight',AccessMode.ReadOnly)
    MinimumTableWidth: float = proxy_property(float,'MinimumTableWidth',AccessMode.ReadOnly)
    RegenerateTableSuppressed: bool = proxy_property(bool,'RegenerateTableSuppressed',AccessMode.ReadWrite)
    RepeatBottomLabels: bool = proxy_property(bool,'RepeatBottomLabels',AccessMode.ReadWrite)
    RowHeight: float = proxy_property(float,'RowHeight',AccessMode.ReadWrite)
    Rows: int = proxy_property(int,'Rows',AccessMode.ReadWrite)
    StyleName: str = proxy_property(str,'StyleName',AccessMode.ReadWrite)
    TableBreakFlowDirection: AcTableFlowDirection = proxy_property('AcTableFlowDirection','TableBreakFlowDirection',AccessMode.ReadWrite)
    TableBreakHeight: float = proxy_property(float,'TableBreakHeight',AccessMode.ReadWrite)
    TableStyleOverrides: AcTableStyleOverrides = proxy_property('AcTableStyleOverrides','TableBreakHeight',AccessMode.ReadWrite)
    TitleSuppressed: bool = proxy_property(bool,'TitleSuppressed',AccessMode.ReadWrite)
    VertCellMargin: float = proxy_property(float,'VertCellMargin',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def ClearSubSelection(self) -> None:
        self._obj.ClearSubSelection()
        
    def ClearTableStyleOverrides(self, flag: int) -> None:
        self._obj.ClearTableStyleOverrides(flag)
        
    def Copy(self, flag: int) -> AcadTable:
        return AcadTable(self._obj.Copy(flag))
            
    def CreateContent(self, nRow: int, nCol: int, nIndex: int) -> int:
        return self._obj.CreateContent(nRow, nCol, nIndex)
        
    def DeleteCellContent(self, row: int, col: int) -> None:
        self._obj.DeleteCellContent(row, col)
        
    def DeleteColumns(self, col: int, cols: int) -> None:
        self._obj.DeleteColumns(col, cols)

    def DeleteContent(self, nRow: int, nCol: int) -> None:
        self._obj.DeleteContent(nRow, nCol)

    def DeleteRows(self, row: int, Rows: int) -> None:
        self._obj.DeleteContent(row, Rows)

    def EnableMergeAll(self, nRow: int, nCol: int, bEnable: bool) -> None:
        self._obj.EnableMergeAll(nRow, nCol, bEnable)

    def FormatValue(self, row: int, col: int, nOption: AcFormatOption) -> str:
        return self._obj.FormatValue(row, col, nOption)

    def GenerateLayout(self) -> None:
        self._obj.GenerateLayout()

    def GetAlignment(self, rowType: AcRowType) -> AcCellAlignment:
        return AcCellAlignment(self._obj.GetAlignment(rowType))

    def GetAttachmentPoint(self, row: int, col: int) -> AcAttachmentPoint:
        return AcAttachmentPoint(self._obj.GetAttachmentPoint(row, col))

    def GetAutoScale(self, row: int, col: int) -> bool:
        return self._obj.GetAutoScale(row, col)

    def GetAutoScale2(self, nRow: int, nCol: int, nContent: int) -> bool:
        return self._obj.GetAutoScale2(nRow, nCol, nContent)

    def GetBackgroundColor(self, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetBackgroundColor(rowType))

    def GetBackgroundColorNone(self, rowType: AcRowType) -> bool:
        return self._obj.GetBackgroundColorNone(rowType)

    def GetBlockAttributeValue(self, row: int, col: int, attdefId: int) -> str:
        return self._obj.GetBlockAttributeValue(row, col, attdefId)

    def GetBlockAttributeValue2(self, nRow: int, nCol: int, nContent: int, blkId: int) -> str:
        return self._obj.GetBlockAttributeValue2(nRow, nCol, nContent, blkId)

    def GetBlockRotation(self, row: int, col: int) -> float:
        return self._obj.GetBlockRotation(row, col)

    def GetBlockScale(self, row: int, col: int) -> float:
        return self._obj.GetBlockScale(row, col)

    def GetBlockTableRecordId(self, row: int, col: int) -> int:
        return self._obj.GetBlockTableRecordId(row, col)

    def GetBlockTableRecordId2(self, nRow: int, nCol: int, nContent: int) -> int:
        return self._obj.GetBlockTableRecordId2(nRow, nCol, nContent)

    def GetBreakHeight(self, nIndex: int) -> float:
        return self._obj.GetBreakHeight(nIndex)

    def GetCellAlignment(self, row: int, col: int) -> AcCellAlignment:
        return AcCellAlignment(self._obj.GetCellAlignment(row, col))

    def GetCellBackgroundColor(self, row: int, col: int) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetCellBackgroundColor(row, col))

    def GetCellBackgroundColorNone(self, row: int, col: int) -> bool:
        return self._obj.GetCellBackgroundColorNone(row, col)

    def GetCellContentColor(self, row: int, col: int) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetCellContentColor(row, col))

    def GetCellDataType(self, row: int, col: int, pDataType: AcValueDataType, pUnitType: AcValueUnitType) -> None:
        self._obj.GetCellDataType(row, col, pDataType, pUnitType)

    def GetCellExtents(self, row: int, col: int, bOuterCell: bool) -> None:
        self._obj.GetCellExtents(row, col, bOuterCell)

    def GetCellFormat(self, row: int, col: int) -> str:
        return self._obj.GetCellFormat(row, col)

    def GetCellGridColor(self, row: int, col: int, edge: AcCellEdgeMask) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetCellGridColor(row, col, edge))

    def GetCellGridLineWeight(self, row: int, col: int, edge: AcCellEdgeMask) -> AcLineWeight:
        return AcLineWeight(self._obj.GetCellGridLineWeight(row, col, edge))

    def GetCellGridVisibility(self, row: int, col: int, edge: AcCellEdgeMask) -> bool:
        return self._obj.GetCellGridVisibility(row, col, edge)

    def GetCellState(self, nRow: int, nCol: int) -> AcCellState:
        return AcCellState(self._obj.GetCellState(nRow, nCol))

    def GetCellStyle(self, nRow: int, nCol: int) -> str:
        return self._obj.GetCellStyle(nRow, nCol)

    def GetCellStyleOverrides(self, row: int, col: int) -> str:
        return self._obj.GetCellStyleOverrides(row, col)

    def GetCellTextHeight(self, row: int, col: int) -> float:
        return self._obj.GetCellTextHeight(row, col)

    def GetCellTextStyle(self, row: int, col: int) -> str:
        return self._obj.GetCellTextStyle(row, col)

    def GetCellType(self, row: int, col: int) -> AcCellType:
        return AcCellType(self._obj.GetCellType(row, col))

    def GetCellValue(self, row: int, col: int) -> Variant:
        return Variant(self._obj.GetCellValue(row, col))

    def GetColumnName(self, nIndex: int) -> str:
        return self._obj.GetColumnName(nIndex)

    def GetColumnWidth(self, col: int) -> float:
        return self._obj.GetColumnWidth(col)

    def GetContentColor(self, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetContentColor(rowType))

    def GetCellContentColor2(self, nRow: int, nCol: int, nContent: int) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetCellContentColor2(nRow, nCol, nContent))

    def GetContentLayout(self, nRow: int, nCol: int) -> AcCellContentLayout:
        return AcCellContentLayout(self._obj.GetContentLayout(nRow, nCol))

    def GetContentType(self, nRow: int, nCol: int) -> AcCellContentType:
        return AcCellContentType(self._obj.GetContentType(nRow, nCol))

    def GetCustomData(self, nRow: int, nCol: int, szKey: str) -> Variant:
        pData = self._obj.GetCustomData(nRow, nCol, szKey)
        return Variant(pData)

    def GetDataFormat(self, nRow: int, nCol: int, nContent: int) -> str:
        return self._obj.GetDataFormat(nRow, nCol, nContent)
    
    def GetDataType(self, rowType: AcRowType) -> tuple[AcValueDataType,AcValueUnitType]:
        pDataType, pUnitType = self._obj.GetDataType(rowType)
        return AcValueDataType(pDataType), AcValueUnitType(pUnitType)
        
    def GetDataType2(self, nRow: int, nCol: int, nContent: int) -> tuple[AcValueDataType,AcValueUnitType]:
        pDataType, pUnitType = self._obj.GetDataType2(nRow, nCol, nContent)
        return AcValueDataType(pDataType), AcValueUnitType(pUnitType)
    
    def GetFieldId(self, row: int, col: int) -> int:
        return self._obj.GetFieldId(row, col)
    
    def GetFieldId2(self, nRow: int, nCol: int, nContent: int) -> int:
        return self._obj.GetFieldId2(nRow, nCol, nContent)

    def GetFormat(self, rowType: AcRowType) -> str:
        return self._obj.GetFormat(rowType)

    def GetFormula(self, nRow: int, nCol: int, nContent: int) -> str:
        return self._obj.GetFormula(nRow, nCol, nContent)

    def GetGridColor(self, gridLineType: AcGridLineType, rowType: AcRowType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetGridColor(gridLineType, rowType))
    
    def GetGridColor2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> AcadAcCmColor:
        return AcadAcCmColor(self._obj.GetGridColor2(nRow, nCol, nGridLineType))
        
    def GetGridDoubleLineSpacing(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> float:
        return self._obj.GetGridDoubleLineSpacing(nRow, nCol, nGridLineType)
        
    def GetGridLineStyle(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> AcGridLineStyle:
        return AcGridLineStyle(self._obj.GetGridLineStyle(nRow, nCol, nGridLineType))
        
    def GetGridLinetype(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> int:
        return self._obj.GetGridLinetype(nRow, nCol, nGridLineType)
            
    def GetGridLineWeight(self, gridLineType: AcGridLineType, rowType: AcRowType) -> AcLineWeight:
        return AcLineWeight(self._obj.GetGridLineWeight(gridLineType, rowType))
        
    def GetGridLineWeight2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> AcLineWeight:
        return AcLineWeight(self._obj.GetGridLineWeight2(nRow, nCol, nGridLineType))
            
    def GetGridVisibility(self, gridLineType: AcGridLineType, rowType: AcRowType) -> bool:
        return self._obj.GetGridVisibility(gridLineType, rowType)
            
    def GetGridVisibility2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType) -> bool:
        return self._obj.GetGridVisibility2(nRow, nCol, nGridLineType)

    def GetHasFormula(self, nRow: int, nCol: int, nContent: int) -> bool:
        return self._obj.GetHasFormula(nRow, nCol, nContent)
    
    def GetMargin(self, nRow: int, nCol: int, nMargin: AcCellMargin) -> float:
        return self._obj.GetMargin(nRow, nCol, nMargin)
        
    def GetMinimumColumnWidth(self, col: int) -> float:
        return self._obj.GetMinimumColumnWidth(col)
        
    def GetMinimumRowHeight(self, row: int) -> float:
        return self._obj.GetMinimumRowHeight(row)

    def GetOverride(self, nRow: int, nCol: int, nContent: int) -> AcCellProperty:
        return AcCellProperty(self._obj.GetOverride(nRow, nCol, nContent))
    
    def GetRotation(self, nRow: int, nCol: int, nContent: int) -> float:
        return self._obj.GetRotation(nRow, nCol, nContent)

    def GetRowHeight(self, row: int) -> float:
        return self._obj.GetRowHeight(row)
    
    def GetRowType(self, row: int) -> AcRowType:
        return AcRowType(self._obj.GetRowType(row))
    
    def GetScale(self, nRow: int, nCol: int, nContent: int) -> float:
        return self._obj.GetScale(nRow, nCol, nContent)
    
    def GetSubSelection(self) -> tuple:
        rowMin, rowMax, colMin, colMax = self._obj.GetSubSelection()
        return rowMin, rowMax, colMin, colMax

    def GetText(self, row: int, col: int) -> str:
        return self._obj.GetText(row, col)
    
    def GetTextHeight(self, rowType: AcRowType) -> float:
        return self._obj.GetTextHeight(rowType)
    
    def GetTextHeight2(self, nRow: int, nCol: int, nContent: int) -> float:
        return self._obj.GetTextHeight2(nRow, nCol, nContent)
        
    def GetTextRotation(self, row: int, col: int) -> AcRotationAngle:
        return AcRotationAngle(self._obj.GetTextRotation(row, col))
        
    def GetTextString(self, nRow: int, nCol: int, nContent: int) -> str:
        return self._obj.GetTextString(nRow, nCol, nContent)
        
    def GetTextStyle(self, rowTypes: AcRowType) -> str:
        return self._obj.GetTextStyle(rowTypes)

    def GetTextStyle2(self, nRow: int, nCol: int, nContent: int) -> str:
        return self._obj.GetTextStyle2(nRow, nCol, nContent)

    def GetValue(self, nRow: int, nCol: int, nContent: int) -> Variant:
        return Variant(self._obj.GetValue(nRow, nCol, nContent))

    def HitTest(self, wpt: PyGePoint3d, wviewVec: PyGeVector3d) -> vIntegerArray:
        resultRowIndex, resultColumnIndex = self._obj.HitTest(wpt(), wviewVec())
        return vIntegerArray(resultRowIndex, resultColumnIndex)

    def InsertColumns(self, col: int, Width: float, cols: int) -> None:
        self._obj.InsertColumns(col, Width, cols)

    def InsertColumnsAndInherit(self, col: int, nInheritFrom: int, nNumCols: int) -> None:
        self._obj.InsertColumnsAndInherit(col, nInheritFrom, nNumCols)

    def InsertRows(self, row: int, Height: float, Rows: int) -> None:
        self._obj.InsertRows(row, Height, Rows)

    def InsertRowsAndInherit(self, nIndex: int, nInheritFrom: int, nNumRows: int) -> None:
        self._obj.InsertRowsAndInherit(nIndex, nInheritFrom, nNumRows)

    def IsContentEditable(self, nRow: int, nCol: int) -> bool:
        return self._obj.IsContentEditable(nRow, nCol)

    def IsEmpty(self, nRow: int, nCol: int) -> bool:
        return self._obj.IsEmpty(nRow, nCol)
    
    def IsFormatEditable(self, nRow: int, nCol: int) -> bool:
        return self._obj.IsFormatEditable(nRow, nCol)
    
    def IsMergeAllEnabled(self, nRow: int, nCol: int) -> bool:
        return self._obj.IsMergeAllEnabled(nRow, nCol)

    def IsMergedCell(self, row: int, col: int, minRow: int, maxRow: int, minCol: int, maxCol: int) -> bool:
        return self._obj.IsMergedCell(row, col, minRow, maxRow, minCol, maxCol)

    def MergeCells(self, minRow: int, maxRow: int, minCol: int, maxCol: int) -> None:
        self._obj.MergeCells(minRow, maxRow, minCol, maxCol)

    def MoveContent(self, nRow: int, nCol: int, nFromIndex: int, nToIndex: int) -> None:
        self._obj.MoveContent(nRow, nCol, nFromIndex, nToIndex)

    def RecomputeTableBlock(self, bForceUpdate: bool) -> None:
        self._obj.RecomputeTableBlock(bForceUpdate)

    def RemoveAllOverrides(self, nRow: int, nCol: int) -> None:
        self._obj.RemoveAllOverrides(nRow, nCol)

    def ReselectSubRegion(self) -> None:
        self._obj.ReselectSubRegion()

    def ResetCellValue(self, row: int, col: int) -> None:
        self._obj.RemoveAllOverrides(row, col)

    def Select(self, wpt: PyGePoint3d, wvwVec: PyGeVector3d, wvwxvec: PyGeVector3d, allowOutside: bool) -> tuple[float,float,int,int]:
        wxaper, wyaper, resultRowIndex, resultColumnIndex = self._obj.RemoveAllOverrides(wpt=wpt(), wvwVec=wvwVec(), wvwxvec=wvwxvec(), allowOutside=allowOutside)
        return float(wxaper), float(wyaper), int(resultRowIndex), int(resultColumnIndex)
    
    def SelectSubRegion(self, wpt1: PyGePoint3d, wpt2: PyGePoint3d, wvwVec: PyGeVector3d, wvwxVec: PyGeVector3d, seltype: AcSelectType, bIncludeCurrentSelection: bool) -> tuple[int,int,int,int]:
        rowMin, rowMax, colMin, colMax = self._obj.RemoveAllOverrides(wpt1(), wpt2(), wvwVec(), wvwxVec(), seltype, bIncludeCurrentSelection)
        return int(rowMin), int(rowMax), int(colMin), int(colMax)

    def SetAlignment(self, rowTypes: AcRowType, cellAlignment: AcCellAlignment) -> None:
        self._obj.SetAlignment(rowTypes, cellAlignment)
    
    def SetAutoScale(self, row: int, col: int, bValue: bool) -> None:
        self._obj.SetAutoScale(row, col, bValue)
    
    def SetAutoScale2(self, nRow: int, nCol: int, nContent: int, bAutoFit: bool) -> None:
        self._obj.SetAutoScale2(nRow, nCol, nContent, bAutoFit)
    
    def SetBackgroundColor(self, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetBackgroundColor(rowTypes, pColor())
    
    def SetBackgroundColorNone(self, rowTypes: AcRowType, bValue: bool) -> None:
        self._obj.SetBackgroundColorNone(rowTypes, bValue)
    
    def SetBlockAttributeValue(self, row: int, col: int, attdefId: int, StringValue: str) -> None:
        self._obj.SetBlockAttributeValue(row, col, attdefId, StringValue)

    def SetBlockAttributeValue2(self, nRow: int, nCol: int, nContent: int, blkId: int, value: str) -> None:
        self._obj.SetBlockAttributeValue2(nRow, nCol, nContent, blkId, value)
    
    def SetBlockRotation(self, row: int, col: int, blkRotation: float) -> None:
        self._obj.SetBlockRotation(row, col, blkRotation)
    
    def SetBlockScale(self, row: int, col: int, blkScale: float) -> None:
        self._obj.SetBlockScale(row, col, blkScale)
    
    def SetBlockTableRecordId(self, row: int, col: int, blkId: int, bAutoFit: bool) -> None:
        self._obj.SetBlockTableRecordId(row, col, blkId, bAutoFit)
    
    def SetBlockTableRecordId2(self, nRow: int, nCol: int, nContent: int, blkId: int, autoFit: bool) -> None:
        self._obj.SetBlockTableRecordId2(nRow, nCol, nContent, blkId, autoFit)
    
    def SetBreakHeight(self, nIndex: int, dHeight: float) -> None:
        self._obj.SetBreakHeight(nIndex, dHeight)
    
    def SetCellAlignment(self, row: int, col: int, cellAlignment: AcCellAlignment) -> None:
        self._obj.SetCellAlignment(row, col, cellAlignment)
    
    def SetCellBackgroundColor(self, row: int, col: int, pColor: AcadAcCmColor) -> None:
        self._obj.SetCellBackgroundColor(row, col, pColor())
    
    def SetCellBackgroundColorNone(self, row: int, col: int, bValue: bool) -> None:
        self._obj.SetCellBackgroundColorNone(row, col, bValue)
    
    def SetCellContentColor(self, row: int, col: int, pColor: AcadAcCmColor) -> None:
        self._obj.SetCellContentColor(row, col, pColor())
    
    def SetCellDataType(self, row: int, col: int, dataType: AcValueDataType, unitType: AcValueUnitType) -> None:
        self._obj.SetCellDataType(row, col, dataType, unitType)
    
    def SetCellFormat(self, row: int, col: int, pFormat: str) -> None:
        self._obj.SetCellFormat(row, col, pFormat)
    
    def SetCellGridColor(self, row: int, col: int, edges: AcCellEdgeMask, pColor: AcadAcCmColor) -> None:
        self._obj.SetCellGridColor(row, col, edges, pColor())
    
    def SetCellGridLineWeight(self, row: int, col: int, edges: AcCellEdgeMask, Lineweight: AcLineWeight) -> None:
        self._obj.SetCellGridColor(row, col, edges, Lineweight)
    
    def SetCellGridVisibility(self, row: int, col: int, edges: AcCellEdgeMask, bValue: bool) -> None:
        self._obj.SetCellGridVisibility(row, col, edges, bValue)
    
    def SetCellState(self, nRow: int, nCol: int, nLock: AcCellState) -> None:
        self._obj.SetCellState(nRow, nCol, nLock)
    
    def SetCellStyle(self, nRow: int, nCol: int, szCellStyle: str) -> None:
        self._obj.SetCellStyle(nRow, nCol, szCellStyle)
    
    def SetCellTextHeight(self, row: int, col: int, TextHeight: float) -> None:
        self._obj.SetCellTextHeight(row, col, TextHeight)
    
    def SetCellTextStyle(self, row: int, col: int, bstrName: str) -> None:
        self._obj.SetCellTextStyle(row, col, bstrName)
    
    def SetCellType(self, row: int, col: int, CellType: AcCellType) -> None:
        self._obj.SetCellType(row, col, CellType)
    
    def SetCellValue(self, row: int, col: int) -> Variant:
        val = self._obj.SetCellValue(row, col)
        return Variant(val)
    
    def SetCellValueFromText(self, row: int, col: int, val: str, nOption: AcParseOption) -> None:
        self._obj.SetCellValueFromText(row, col, val, nOption)
    
    def SetColumnName(self, nIndex: int, name: str) -> None:
        self._obj.SetColumnName(nIndex, name)
    
    def SetColumnWidth(self, col: int, Width: float) -> None:
        self._obj.SetColumnWidth(col, Width)
    
    def SetContentColor(self, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetContentColor(rowTypes, pColor())
    
    def SetContentColor2(self, nRow: int, nCol: int, nContent: int, pColor: AcadAcCmColor) -> None:
        self._obj.SetContentColor2(nRow, nCol, nContent, pColor())
    
    def SetContentLayout(self, nRow: int, nCol: int, nLayout: AcCellContentLayout) -> None:
        self._obj.SetContentLayout(nRow, nCol, nLayout)
    
    def SetCustomData(self, nRow: int, nCol: int, szKey: str, data: Variant) -> None:
        self._obj.SetCustomData(nRow, nCol, szKey, data())
    
    def SetDataFormat(self, nRow: int, nCol: int, nContent: int, szFormat: str) -> None:
        self._obj.SetDataFormat(nRow, nCol, nContent, szFormat)
    
    def SetDataType(self, rowTypes: AcRowType, nDataType: AcValueDataType, nUnitType: AcValueUnitType) -> None:
        self._obj.SetDataType(rowTypes, nDataType, nUnitType)
    
    def SetDataType2(self, nRow: int, nCol: int, nContent: int, dataType: AcValueDataType, unitType: AcValueUnitType) -> None:
        self._obj.SetDataType2(nRow, nCol, nContent, dataType, unitType)
    
    def SetFieldId(self, row: int, col: int, fieldId: int) -> None:
        self._obj.SetFieldId(row, col, fieldId)
    
    def SetFieldId2(self, nRow: int, nCol: int, nContent: int, acDbObjectId: int, nflag: AcCellOption) -> None:
        self._obj.SetFieldId2(nRow, nCol, nContent, acDbObjectId, nflag)
    
    def SetFormat(self, rowTypes: AcRowType, pFormat: str) -> None:
        self._obj.SetFormat(rowTypes, pFormat)
    
    def SetFormula(self, nRow: int, nCol: int, nContent: int, pszFormula: str) -> None:
        self._obj.SetFormula(nRow, nCol, nContent, pszFormula)
    
    def SetGridColor(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, pColor: AcadAcCmColor) -> None:
        self._obj.SetGridColor(gridLineTypes, rowTypes, pColor())
    
    def SetGridColor2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, pColor: AcadAcCmColor) -> None:
        self._obj.SetGridColor2(nRow, nCol, nGridLineType, pColor())
    
    def SetGridDoubleLineSpacing(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, fSpacing: float) -> None:
        self._obj.SetGridDoubleLineSpacing(nRow, nCol, nGridLineType, fSpacing)
    
    def SetGridLineStyle(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, nLineStyle: AcGridLineStyle) -> None:
        self._obj.SetGridLineStyle(nRow, nCol, nGridLineType, nLineStyle)
    
    def SetGridLinetype(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, idLinetype: int) -> None:
        self._obj.SetGridLinetype(nRow, nCol, nGridLineType, idLinetype)
    
    def SetGridLineWeight(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, Lineweight: AcLineWeight) -> None:
        self._obj.SetGridLineWeight(gridLineTypes, rowTypes, Lineweight)
    
    def SetGridLineWeight2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, lineWeight: AcLineWeight) -> None:
        self._obj.SetGridLineWeight2(nRow, nCol, nGridLineType, lineWeight)
    
    def SetGridVisibility(self, gridLineTypes: AcGridLineType, rowTypes: AcRowType, bValue: bool) -> None:
        self._obj.SetGridVisibility(gridLineTypes, rowTypes, bValue)
    
    def SetGridVisibility2(self, nRow: int, nCol: int, nGridLineType: AcGridLineType, bVisible: bool) -> None:
        self._obj.SetGridVisibility2(nRow, nCol, nGridLineType, bVisible)
    
    def SetMargin(self, nRow: int, nCol: int, nMargins: AcCellMargin, fMargin: float) -> None:
        self._obj.SetMargin(nRow, nCol, nMargins, fMargin)
    
    def SetOverride(self, nRow: int, nCol: int, nContent: int, nProp: AcCellProperty) -> None:
        self._obj.SetOverride(nRow, nCol, nContent, nProp)
    
    def SetRotation(self, nRow: int, nCol: int, nContent: int, pValue: float) -> None:
        self._obj.SetRotation(nRow, nCol, nContent, pValue)
    
    def SetRowHeight(self, row: int, Height: float) -> None:
        self._obj.SetRowHeight(row, Height)
    
    def SetScale(self, nRow: int, nCol: int, nContent: int, scale: float) -> None:
        self._obj.SetScale(nRow, nCol, nContent, scale)
    
    def SetSubSelection(self, rowMin: int, rowMax: int, colMin: int, colMax: int) -> None:
        self._obj.SetSubSelection(rowMin, rowMax, colMin, colMax)
    
    def SetText(self, row: int, col: int, pStr: str) -> None:
        self._obj.SetText(row, col, pStr)
    
    def SetTextHeight(self, rowTypes: AcRowType, TextHeight: float) -> None:
        self._obj.SetTextHeight(rowTypes, TextHeight)
    
    def SetTextHeight2(self, nRow: int, nCol: int, nContent: int, height: float) -> None:
        self._obj.SetTextHeight2(nRow, nCol, nContent, height)
    
    def SetTextRotation(self, row: int, col: int, TextRotation: AcRotationAngle) -> None:
        self._obj.SetTextRotation(row, col, TextRotation)
    
    def SetTextString(self, nRow: int, nCol: int, nContent: int, text: str) -> None:
        self._obj.SetTextString(nRow, nCol, nContent, text)
    
    def SetTextStyle(self, rowTypes: AcRowType, bstrName: str) -> None:
        self._obj.SetTextStyle(rowTypes, bstrName)
    
    def SetTextStyle2(self, nRow: int, nCol: int, nContent: int, StringStyleName: str) -> None:
        self._obj.SetTextStyle2(nRow, nCol, nContent, StringStyleName)
    
    def SetToolTip(self, nRow: int, nCol: int, tip: str) -> None:
        self._obj.SetToolTip(nRow, nCol, tip)
    
    def SetValue(self, nRow: int, nCol: int, nContent: int, acValue: Variant) -> None:
        self._obj.SetValue(nRow, nCol, nContent, acValue())
    
    def SetValueFromText(self, nRow: int, nCol: int, nContent: int, szText: str, nOption: AcParseOption) -> None:
        self._obj.SetValueFromText(nRow, nCol, nContent, szText, nOption)
    
    def UnmergeCells(self, minRow: int, maxRow: int, minCol: int, maxCol: int) -> None:
        self._obj.UnmergeCells(minRow, maxRow, minCol, maxCol)