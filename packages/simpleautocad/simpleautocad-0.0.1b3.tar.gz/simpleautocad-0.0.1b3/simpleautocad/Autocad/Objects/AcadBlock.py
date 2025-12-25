from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from ..Objects import *
from ..AcadEntity import *
from ..Entities import *


class IAcadBlock(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add3DFace(self, Point1: PyGePoint3d, 
                        Point2: PyGePoint3d, 
                        Point3: PyGePoint3d, 
                        Point4: PyGePoint3d = None) -> Acad3DFace:
        return Acad3DFace(self._obj.Add3DFace(Point1(), Point2(), Point3(), Point4()))

    def Add3DMesh(self, M: int, 
                        N: int, 
                        PointsMatrix: vDoubleArray) -> AcadPolygonMesh:
        return AcadPolygonMesh(self._obj.Add3DMesh(M, N, PointsMatrix()))

    def Add3DPoly(self, PointsArray: PyGePoint3dArray) -> Acad3DPolyline:
        return Acad3DPolyline(self._obj.Add3Dpoly(PointsArray()))
        
    def AddArc(self, Center: PyGePoint3d, 
                        Radius: float, 
                        StartAngle: float, 
                        EndAngle: float) -> AcadArc:
        return AcadArc(self._obj.AddArc(Center(), Radius, StartAngle, EndAngle))

    def AddAttribute(self, Height: float, 
                        Mode: AcAttributeMode, 
                        Prompt: str, 
                        InsertionPoint: PyGePoint3d, 
                        Tag: str, 
                        Value: str) -> AcadAttribute:
        return AcadAttribute(self._obj.AddAttribute(Height, Mode.value, Prompt, InsertionPoint(), Tag, Value))
        
    def AddBox(self, Origin: PyGePoint3d, 
                        Length: float, 
                        Width: float, 
                        Height: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddBox(Origin(), Length, Width, Height))

    def AddCircle(self, Center: PyGePoint3d, 
                        Radius: float) -> AcadCircle:
        return AcadCircle(self._obj.AddCircle(Center(), Radius))
    
    def AddCone(self, Center: PyGePoint3d, 
                        BaseRadius: float, 
                        Height: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddCone(Center(), BaseRadius, Height))

    def AddCustomObject(self, ClassName: str) -> AcadObject:
        return AcadObject(self._obj.AddCustomObject(ClassName))

    def AddCylinder(self, Center: PyGePoint3d, 
                        Radius: float, 
                        Height: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddCylinder(Center(), Radius, Height))

    def AddDim3PointAngular(self, AngleVertex: PyGePoint3d, 
                        FirstEndPoint: PyGePoint3d, 
                        SecondEndPoint: PyGePoint3d, 
                        TextPoint: PyGePoint3d) -> AcadDim3PointAngular:
        return AcadDim3PointAngular(self._obj.AddDim3PointAngular(AngleVertex(), FirstEndPoint(), SecondEndPoint(), TextPoint()))

    def AddDimAligned(self, ExtLine1Point: PyGePoint3d, 
                        ExtLine2Point: PyGePoint3d, 
                        TextPosition: PyGePoint3d) -> AcadDimAligned:
        return AcadDimAligned(self._obj.AddDimAligned(ExtLine1Point(), ExtLine2Point(), TextPosition()))

    def AddDimArc(self, ArcCenter: PyGePoint3d, 
                        FirstEndPoint: PyGePoint3d, 
                        SecondEndPoint: PyGePoint3d, 
                        ArcPoint: PyGePoint3d) -> AcadDimArcLength:
        return AcadDimArcLength(self._obj.AddDimArc(ArcCenter(), FirstEndPoint(), SecondEndPoint(), ArcPoint()))

    def AddDimDiametric(self, ChordPoint: PyGePoint3d, 
                        FarChordPoint: PyGePoint3d, 
                        LeaderLength: float) -> AcadDimDiametric:
        return AcadDimDiametric(self._obj.AddDimDiametric(ChordPoint(), FarChordPoint(), LeaderLength))

    def AddDimOrdinate(self, DefinitionPoint: PyGePoint3d, 
                        LeaderEndPoint: PyGePoint3d, 
                        UseXAxis: bool) -> AcadDimOrdinate:
        return AcadDimOrdinate(self._obj.AddDimOrdinate(DefinitionPoint, LeaderEndPoint, UseXAxis))

    def AddDimRadial(self, Center: PyGePoint3d, 
                        ChordPoint: PyGePoint3d, 
                        LeaderLength: float) -> AcadDimRadial:
        return AcadDimRadial(self._obj.AddDimRadial(Center(), ChordPoint(), LeaderLength))

    def AddDimRadialLarge(self, Center: PyGePoint3d, 
                        ChordPoint: PyGePoint3d, 
                        OverrideCenter: PyGePoint3d, 
                        JogPoint: PyGePoint3d, 
                        JogAngle: float) -> AcadDimRadialLarge:
        return AcadDimRadialLarge(self._obj.AddDimRadialLarge(Center(), ChordPoint(), OverrideCenter(), JogPoint(), JogAngle))

    def AddDimRotated(self, XLine1Point: PyGePoint3d, 
                        XLine2Point: PyGePoint3d, 
                        DimLineLocation: PyGePoint3d, 
                        RotationAngle: float) -> AcadDimRotated:
        return AcadDimRotated(self._obj.AddDimRotated(XLine1Point(), XLine2Point(), DimLineLocation(), RotationAngle))

    def AddEllipse(self, Center: PyGePoint3d, 
                        MajorAxis: PyGeVector3d, 
                        RadiusRatio: float) -> AcadEllipse:
        return AcadEllipse(self._obj.AddEllipse(Center(), MajorAxis(), RadiusRatio))

    def AddEllipticalCone(self, Center: PyGePoint3d, 
                        MajorRadius: float, 
                        MinorRadius: float, 
                        Height: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddEllipticalCone(Center(), MajorRadius, MinorRadius, Height))

    def AddEllipticalCylinder(self, Center: PyGePoint3d, 
                        MajorRadius: float, 
                        MinorRadius: float, 
                        Height: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddEllipticalCylinder(Center(), MajorRadius, MinorRadius, Height))

    def AddExtrudedSolid(self, Profile: AcadRegion, 
                        Height: float, 
                        TaperAngle: float) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddExtrudedSolid(Profile(), Height, TaperAngle))

    def AddExtrudedSolidAlongPath(self, Profile: AcadRegion, 
                        Path: AcadArc|AcadCircle|AcadEllipse|AcadPolyline|AcadSpline) -> Acad3DSolid:
        return Acad3DSolid(self._obj.AddExtrudedSolidAlongPath(Profile(), Path))

    def AddHatch(self, PatternType: AcPatternType|AcGradientPatternType, 
                        PatternName: str, 
                        Associativity: bool, 
                        HatchObjectType: AcHatchObjectType = None) -> AcadHatch:
        return AcadHatch(self._obj.AddHatch(PatternType, PatternName, Associativity, HatchObjectType))

    def AddLeader(self, PointsArray: PyGePoint3d, 
                        Annotation: AcadBlockReference|AcadMtext|AcadTolerance, 
                        Type: AcLeaderType) -> AcadLeader:
        return AcadLeader(self._obj.AddLeader(PointsArray(), Annotation, Type))

    def AddLightWeightPolyline(self, VerticesList: PyGePoint2dArray) -> AcadLWPolyline:
        return AcadLWPolyline(self._obj.AddLightWeightPolyline(VerticesList()))

    def AddLine(self, StartPoint: PyGePoint3d, 
                        EndPoint: PyGePoint3d) -> AcadLine: 
        return AcadLine(self._obj.AddLine(StartPoint(), EndPoint()))

    def AddMInsertBlock(self, InsertionPoint: PyGePoint3d, 
                        Name: str, 
                        XScale: float, 
                        YScale: float, 
                        ZScale: float, 
                        Rotation: float, 
                        NumRows: int, 
                        NumColumns: int, 
                        RowSpacing: float, 
                        ColumnSpacing: float, 
                        Password: Variant = vObjectEmpty) -> AcadMInsertBlock: 
        return AcadMInsertBlock(self._obj.AddMInsertBlock(InsertionPoint(), Name, XScale, YScale, ZScale, Rotation, NumRows, NumColumns, RowSpacing, ColumnSpacing, Password()))

    def AddMLeader(self, pointsArray: PyGePoint3dArray) -> AcadMLeader: 
        return AcadMLeader(*self._obj.AddMLeader(pointsArray()))

    def AddMLine(self, VertexList: PyGePoint3dArray) -> AcadMLine: 
        return AcadMLine(self._obj.AddMLine(VertexList()))

    def AddMText(self, InsertionPoint: PyGePoint3d, 
                        Width: float, 
                        Text: str) -> AcadMtext: 
        return AcadMtext(self._obj.AddMText(InsertionPoint(), Width, Text))

    def AddPoint(self, Point: PyGePoint3d) -> AcadPoint: 
        return AcadPoint(self._obj.AddPoint(Point()))

    def AddPolyfaceMesh(self, VerticesList: PyGePoint3dArray, 
                        FaceList: vShortArray) -> AcadPolyfaceMesh: 
        return AcadPolyfaceMesh(self._obj.AddPolyfaceMesh(VerticesList(), FaceList()))

    def AddPolyline(self, VerticesList: PyGePoint3dArray) -> AcadPolyline: 
        return AcadPolyline(self._obj.AddPolyline(VerticesList()))

    def AddRaster(self, ImageFileName: str, 
                        InsertionPoint: PyGePoint3d, 
                        ScaleFactor: float, 
                        RotationAngle: float) -> AcadRasterImage: 
        return AcadRasterImage(self._obj.AddRaster(ImageFileName, InsertionPoint(), ScaleFactor, RotationAngle))

    def AddRay(self, Point1: PyGePoint3d, 
                        Point2: PyGePoint3d) -> AcadRay: 
        return AcadRay(self._obj.AddRay(Point1(), Point2()))

    def AddRegion(self, ObjectList: vObjectArray[AcadArc|AcadCircle|AcadEllipse|AcadLine|AcadLWPolyline|AcadSpline]) -> vObjectArray[AcadRegion]: 
        return vObjectArray([AcadRegion(region) for region in self._obj.AddRegion(ObjectList())])

    def AddRevolvedSolid(self, Profile: AcadRegion, 
                        AxisPoint: PyGePoint3d, 
                        AxisDir: PyGeVector3d, 
                        Angle: float) -> Acad3DSolid: 
        return Acad3DSolid(self._obj.AddRevolvedSolid(Profile, AxisPoint(), AxisDir(), Angle))

    def AddSection(self, FromPoint: PyGePoint3d, 
                        ToPoint: PyGePoint3d, 
                        planeVector: PyGeVector3d) -> AcadSection: 
        return AcadSection(self._obj.AddSection(FromPoint(), ToPoint(), planeVector()))

    def AddShape(self, Name: str, 
                        InsertionPoint: PyGePoint3d, 
                        ScaleFactor: float, 
                        Rotation: float) -> AcadShape: 
        return AcadShape(self._obj.AddShape(Name, InsertionPoint(), ScaleFactor, Rotation))

    def AddSolid(self, Point1: PyGePoint3d, 
                        Point2: PyGePoint3d, 
                        Point3: PyGePoint3d, 
                        Point4: PyGePoint3d) -> AcadSolid: 
        return AcadSolid(self._obj.AddSolid(Point1(), Point2(), Point3(), Point4()))

    def AddSphere(self, Center: PyGePoint3d, 
                        Radius: float) -> Acad3DSolid: 
        return Acad3DSolid(self._obj.AddSphere(Center(), Radius))

    def AddSpline(self, PointsArray: PyGePoint3dArray, 
                        StartTangent: PyGeVector3d, 
                        EndTangent: PyGeVector3d) -> AcadSpline: 
        return AcadSpline(self._obj.AddSpline(PointsArray(), StartTangent(), EndTangent()))

    def AddTable(self, InsertionPoint: PyGePoint3d, 
                        NumRows: int, 
                        NumColumns: int, 
                        RowHeight: float, 
                        ColWidth: float) -> AcadTable: 
        return AcadTable(self._obj.AddTable(InsertionPoint(), NumRows, NumColumns, RowHeight, ColWidth))

    def AddText(self, TextString: str, 
                        InsertionPoint: PyGePoint3d, 
                        Height: float) -> AcadText: 
        return AcadText(self._obj.AddText(TextString, InsertionPoint(), Height))

    def AddTolerance(self, Text: str, 
                        InsertionPoint: PyGePoint3d, 
                        Direction: PyGeVector3d) -> AcadTolerance: 
        return AcadTolerance(self._obj.AddTolerance(Text, InsertionPoint(), Direction()))

    def AddTorus(self, Center: PyGePoint3d, 
                        TorusRadius: float, 
                        TubeRadius: float) -> Acad3DSolid: 
        return Acad3DSolid(self._obj.AddTorus(Center(), TorusRadius, TubeRadius))

    def AddTrace(self, PointsArray: PyGePoint3dArray) -> AcadTrace: 
        return AcadTrace(self._obj.AddTrace(PointsArray()))

    def AddWedge(self, Center: PyGePoint3d, 
                        Length: float, 
                        Width: float, 
                        Height: float) -> Acad3DSolid: 
        return Acad3DSolid(self._obj.AddWedge(Center(), Length, Width, Height))

    def AddXline(self, Point1: PyGePoint3d, 
                        Point2: PyGePoint3d) -> AcadXline: 
        return AcadXline(self._obj.AddXline(Point1(), Point2()))

    def AttachExternalReference(self,PathName: str, 
                        Name: str, 
                        InsertionPoint: PyGePoint3d, 
                        XScale: float,
                        YScale: float,
                        ZScale: float,
                        Rotation: float,
                        Overlay: bool,
                        Password: Variant = vObjectEmpty) -> AcadExternalReference: 
        return AcadExternalReference(self._obj.AttachExternalReference(PathName, Name, InsertionPoint(), XScale, YScale, ZScale, Rotation, Overlay, Password()))

    def InsertBlock(self, InsertionPoint: PyGePoint3d, 
                        Name: str, 
                        Xscale: float = 1.0, 
                        Yscale: float = 1.0, 
                        ZScale: float = 1.0, 
                        Rotation: float = 0.0, 
                        Password: Variant = vObjectEmpty) -> AcadBlockReference:
        return AcadBlockReference(self._obj.InsertBlock(InsertionPoint(), Name, Xscale, Yscale, ZScale, Rotation, Password()))

class AcadBlock(IAcadBlock):
    def __init__(self, obj) -> None: super().__init__(obj)

    BlockScaling: AcBlockScaling = proxy_property('AcBlockScaling','BlockScaling',AccessMode.ReadWrite)
    Comments: str = proxy_property(str,'Comments',AccessMode.ReadWrite)
    Explodable: bool = proxy_property(bool,'Explodable',AccessMode.ReadWrite)
    IsDynamicBlock: bool = proxy_property(bool,'IsDynamicBlock',AccessMode.ReadOnly)
    IsLayout: bool = proxy_property(bool,'IsLayout',AccessMode.ReadOnly)
    IsXRef: bool = proxy_property(bool,'IsXRef',AccessMode.ReadOnly)
    Layout: AcadLayout = proxy_property('AcadLayout','Layout',AccessMode.ReadWrite)
    Material: str = proxy_property(str,'Material',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)
    Origin: PyGePoint3d = proxy_property('PyGePoint3d','Origin',AccessMode.ReadWrite)
    Path: str = proxy_property(str,'Path',AccessMode.ReadWrite)
    Units: AcInsertUnits = proxy_property('AcInsertUnits','Units',AccessMode.ReadWrite)
    XRefDatabase: AcadDatabase = proxy_property('AcadDatabase','XRefDatabase',AccessMode.ReadOnly)

    def Bind(self, bPrefixName: bool) -> None:
        self._obj.Bind(bPrefixName)

    def Delete(self) -> None:
        self._obj.Delete()

    def Detach(self) -> None:
        self._obj.Detach()

    def Reload(self) -> None:
        self._obj.Reload()

    def Unload(self) -> None:
        self._obj.Unload()
