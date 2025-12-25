from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadSpline(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    Closed: bool = proxy_property(bool,'Closed',AccessMode.ReadOnly)
    Closed2: bool = proxy_property(bool,'Closed2',AccessMode.ReadWrite)
    ControlPoints: PyGePoint3dArray = proxy_property('PyGePoint3dArray','ControlPoints',AccessMode.ReadWrite)
    Degree: int = proxy_property(int,'Degree',AccessMode.ReadOnly)
    Degree2: int = proxy_property(int,'Degree2',AccessMode.ReadWrite)
    EndTangent: PyGeVector3d = proxy_property('PyGeVector3d','EndTangent',AccessMode.ReadWrite)
    FitPoints: PyGePoint3dArray = proxy_property('PyGePoint3dArray','FitPoints',AccessMode.ReadWrite)
    FitTolerance: float = proxy_property(float,'FitTolerance',AccessMode.ReadWrite)
    IsPeriodic: bool = proxy_property(bool,'IsPeriodic',AccessMode.ReadOnly)
    IsPlanar: bool = proxy_property(bool,'IsPlanar',AccessMode.ReadOnly)
    IsRational: bool = proxy_property(bool,'IsRational',AccessMode.ReadOnly)
    KnotParameterization: AcSplineKnotParameterizationType = proxy_property('AcSplineKnotParameterizationType','KnotParameterization',AccessMode.ReadWrite)
    Knots: PyGeVector3d = proxy_property('PyGeVector3d','Knots',AccessMode.ReadWrite)
    NumberOfControlPoints: int = proxy_property(int,'NumberOfControlPoints',AccessMode.ReadOnly)
    NumberOfFitPoints: int = proxy_property(int,'NumberOfFitPoints',AccessMode.ReadOnly)
    SplineFrame: AcSplineFrameType = proxy_property('AcSplineFrameType','SplineFrame',AccessMode.ReadWrite)
    SplineMethod: AcSplineMethodType = proxy_property('AcSplineMethodType','SplineMethod',AccessMode.ReadWrite)
    StartTangent: PyGeVector3d = proxy_property('PyGeVector3d','StartTangent',AccessMode.ReadWrite)
    Weights: PyGeVector3d = proxy_property('PyGeVector3d','Weights',AccessMode.ReadWrite)

    def AddFitPoint(self, Index: int, FitPoint: PyGePoint3d) -> None:
        self._obj.AddFitPoint(Index, FitPoint())
    
    def Copy(self) -> AcadSpline:
        return AcadSpline(self._obj.Copy())
        
    def DeleteFitPoint(self, Index: int) -> None:
        self._obj.DeleteFitPoint(Index)
        
    def ElevateOrder(self, Order: int) -> None:
        self._obj.ElevateOrder(Order)

    def GetControlPoint(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.GetControlPoint(Index))
        
    def GetFitPoint(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.GetFitPoint(Index))
        
    def GetWeight(self, Index: int) -> int:
        return self._obj.GetWeight(Index)
            
    def Offset(self, Distance: float) -> AcadSpline:
        return AcadSpline(self._obj.Offset(Distance))
        
    def PurgeFitData(self) -> None:
        self._obj.PurgeFitData()
            
    def Reverse(self) -> None:
        self._obj.Reverse()
                
    def SetControlPoint(self, Index: int, Value: PyGePoint3d) -> None:
        self._obj.SetControlPoint(Index, Value)
    
    def SetFitPoint(self, Index: int, Value: PyGePoint3d) -> None:
        self._obj.SetFitPoint(Index, Value)

    def SetWeight(self, Index: int, Weight: float) -> None:
        self._obj.SetWeight(Index, Weight)
