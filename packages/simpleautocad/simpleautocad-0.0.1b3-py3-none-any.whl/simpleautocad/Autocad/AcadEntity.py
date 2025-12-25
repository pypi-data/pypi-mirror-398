from __future__ import annotations
from .Base import *
from .Proxy import *
from .AcadObject import *
from .Objects import *



class AcadEntity(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    EntityTransparency: AcEntityTransparency = proxy_property(str,'EntityTransparency',AccessMode.ReadWrite)
    """Specifies the transparency value for the entity.

    object 
        Type: All drawing objects 
        The object this property applies to. 
    Property Value
        Read-only: No 
        Type: String 
        Use one of the following values: 
        ByLayer: Transparency value determined by layer 
        ByBlock: Transparency value determined by block 
        0: Fully opaque (not transparent) 
        1-90: Transparency value defined as a percentage 
    Remarks
        When representing a percentage of transparency for an entity, the string value is of an integer and not a double. 
    """

    Hyperlinks: AcadHyperlinks = proxy_property('AcadHyperlinks','Hyperlinks',AccessMode.ReadOnly)
    """Gets the Hyperlinks collection for an entity.

    object 
        Type: All drawing objects, AttributeReference, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Hyperlinks 
        The Hyperlinks collection for the entity. 
    Remarks
        No additional remarks. 
    """

    Layer: str = proxy_property(str,'Layer',AccessMode.ReadWrite)
    """Specifies the layer for an object.

    object 
        Type: All drawing objects, AttributeReference, Group, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: No; except for the Group object which is write-only 
        Type: String 
        The name of the layer. 
    Remarks
        All objects have an associated layer. The document always contains at least one layer (layer 0). As with linetypes, you can specify a layer for an object. If you do not specify a layer, the current active layer is used for a new object. If a layer is specified for an object, the current active layer is ignored. Use the ActiveLayer property to set or query the current active layer.
        Each layer has associated properties that can be set and queried through the Layer object. 
    """

    Linetype: str = proxy_property(str,'Linetype',AccessMode.ReadWrite)
    """Specifies the linetype of an object.

    object 
        Type: All drawing objects, AttributeReference, Group, Layer, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: No; except for Group objects which are write-only 
        Type: String 
        The linetype of an object. The default linetype is the linetype of the layer (ByLayer). 
        Continuous: The default linetype, which is automatically created in the linetype symbol table. 
        ByLayer: The linetype value of the object's layer. 
        ByBlock: The linetype value of the object's surrounding block definition's current block reference. 
    Remarks
        The linetype values identify the series of dots and dashes used for drawing lines. If you do not specify a linetype, the current active linetype is used for a new entity. If a linetype is specified for an entity, the current active linetype is ignored. Use the ActiveLinetype property to set or query the current active linetype.
        NoteIt is not possible to create a linetype programmatically. An existing linetype may be added to a drawing by using the Load method to first load the linetype, and then the Add method to add it to the Linetypes collection. 
    """

    LinetypeScale: float = proxy_property(float,'LinetypeScale',AccessMode.ReadWrite)
    """Specifies the linetype scale of an object.

    object 
        Type: All drawing objects, AttributeReference, Group, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: No; except for a Group object which is write-only 
        Type: Double 
        This value must be a positive real number. The default is 1.0. 
    Remarks
        The linetype scale of an object specifies the relative length of dash-dot linetypes per drawing unit. 
        ----.----: Linetype scale = 1.0 
        --.--.--.: Linetype scale = 0.5 
        -.-.-.-.-: Linetype scale = 0.25 
    """

    Lineweight: AcLineWeight = proxy_property('AcLineWeight','Lineweight',AccessMode.ReadWrite)
    """Specifies the lineweight of an individual object or the default lineweight for the drawing.

    object 
        Type: All drawing objects, DatabasePreferences, Layer, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: No 
        Type: acLineWeight enum 
        acLnWtByLayer 
        acLnWtByBlock 
        acLnWtByLwDefault 
        acLnWt000 
        acLnWt005 
        acLnWt009 
        acLnWt013 
        acLnWt015 
        acLnWt018 
        acLnWt020 
        acLnWt025 
        acLnWt030 
        acLnWt035 
        acLnWt040 
        acLnWt050 
        acLnWt053 
        acLnWt060 
        acLnWt070 
        acLnWt080 
        acLnWt090 
        acLnWt100 
        acLnWt106 
        acLnWt120 
        acLnWt140 
        acLnWt158 
        acLnWt200 
        acLnWt211 
    Remarks
        The initial value for this property is acLnWtByBlock. 
        Lineweight values consist of standard settings including BYLAYER, BYBLOCK, and DEFAULT. The DEFAULT value is set by the LWDEFAULT system variable and defaults to a value of 0.01 in. or 0.25 mm. All new objects and layers have a default setting of DEFAULT. The lineweight value of 0 plots at the thinnest lineweight available on the specified plotting device and is displayed at one pixel wide in model space. 
    """

    Material: str = proxy_property(str,'Material',AccessMode.ReadWrite)
    """Specifies the name of the material.

    object 
        Type: All drawing objects, AttributeReference, Group, Layer, SubDMeshFace, SubEntSolidFace 
        The objects this property applies to. 
    Property Value
        Read-only: No 
        Type: String 
        The name of the material. 
    Remarks
        No additional remarks.
    """

    PlotStyleName: str = proxy_property(str,'PlotStyleName',AccessMode.ReadWrite)
    """Specifies the plot style name for an object, group of objects, or layer.

    object 
        Type: All drawing objects, AttributeReference, Dimension, Group, Layer, MLeaderLeader, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex 
        The objects this property applies to. 
    Property Value
        Read-only: No; except the Group object which is write-only 
        Type: String 
        The plot style name for the object. 
    Remarks
        No additional remarks.
    """

    TrueColor: AcadAcCmColor = proxy_property('AcadAcCmColor','TrueColor',AccessMode.ReadWrite)
    """Specifies the True Color of an object.

    object 
        Type: All drawing objects, AttributeReference, Dimension, Group, Layer 
        The objects this property applies to. 
    Property Value
        Read-only: No 
        Type: AcCmColor 
        The True Color object of the object. 
    Remarks
        This property is used to change an object's color. Colors are identified by an AcCmColor object. This object can hold an RGB value, an ACI number (an integer from 1 to 255), or a named color. Using an RGB value, you can choose from millions of colors.
    """

    Visible: bool = proxy_property(bool,'Visible',AccessMode.ReadWrite)
    """Specifies the visibility of an object or the application.

    object 
        Type: All drawing objects, Application, AttributeReference, Group, Toolbar 
        The objects this property applies to 
    Property Value
        Read-only: No (except for a Group object which is write-only) 
        Type: Boolean 
        True: The object or application is visible. 
        False: The object or application is not visible. 
    Remarks
        If you specify an object to be invisible, it will be invisible regardless of the application visible setting. Other factors can also cause an object to be invisible; for example, an object will not be displayed if its layer is off or frozen. 
        Specifying the application to be invisible allows you to run tasks in the background without having to see the component.
    """

    def ArrayPolar(self, NumberOfObjects: int, AngleToFill: float, CenterPoint: PyGePoint3d) -> vObjectArray:
        """Creates a polar array of objects given a NumberOfObjects, AngleToFill, and CenterPoint.

        object 
            Type: All drawing objects 
            The objects this method applies to. 
        NumberOfObjects 
            Access: Input-only 
            Type: Long 
            The number of objects to be created in the polar array. This must be a positive integer greater than 1. 
        AngleToFill 
            Access: Input-only 
            Type: Double 
            The angle to fill in radians. A positive value specifies counterclockwise rotation. A negative value specifies clockwise rotation. An error is returned for an angle that equals 0. 
        CenterPoint 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the center point for the polar array. 
        Return Value (RetVal)
            Type: Variant (array of objects) 
            The array of new objects. 
        Remarks
            AutoCAD determines the distance from the array's center point to a reference point on the last object selected. The reference point used depends on the type of object previously selected. AutoCAD uses the center point of a circle or arc, the insertion point of a block or shape, the start point of text, and one endpoint of a line or trace.
            Note that this method does not support the Rotate While Copying option of the AutoCAD ARRAY command.
            NoteYou cannot execute this method while simultaneously iterating through a collection. An iteration will open the work space for a read-only operation, while this method attempts to perform a read-write operation. Complete any iteration before you call this method. 
            AttributeReference: You should not attempt to use this method on AttributeReference objects. AttributeReference objects inherit this method because they are one of the drawing objects, however, it is not feasible to perform this operation on an attribute reference.
        """
        return self._obj.ArrayPolar(NumberOfObjects, AngleToFill, CenterPoint())

    def ArrayRectangular(self, NumberOfRows: int, NumberOfColumns: int, NumberOfLevels: int, DistBetweenRows: float, DistBetweenColumns: float, DistBetweenLevels: float) -> vObjectArray:
        """Creates a 2D or 3D rectangular array of objects.
        
        object 
            Type: All drawing objects 
            The objects this method applies to. 
        NumberOfRows 
            Access: Input-only 
            Type: Long 
            The number of rows in the rectangular array. This must be a positive number. If this number is 1, then NumberOfColumns must be greater than 1. 
        NumberOfColumns 
            Access: Input-only 
            Type: Long 
            The number of columns in the rectangular array. This must be a positive number. If this number is 1, then NumberOfRows must be greater than 1. 
        NumberOfLevels 
            Access: Input-only 
            Type: Long 
            The number of levels in a 3D array. 
        DistBetweenRows 
            Access: Input-only 
            Type: Double 
            The distance between the rows. If the distance between rows is a positive number, rows are added upward from the base entity. If the distance is a negative number, rows are added downward. 
        DistBetweenColumns 
            Access: Input-only 
            Type: Double 
            The distance between the columns. If the distance between columns is a positive number, columns are added to the right of the base entity. If the distance is a negative number, columns are added to the left. 
        DistBetweenLevels 
            Access: Input-only 
            Type: Double 
            The distance between the array levels. If the distance between levels is a positive number, levels are added in the positive direction from the base entity. If the distance is a negative number, levels are added in the negative direction. 
        Return Value (RetVal)
            Type: Variant (array of objects) 
            The array of newly created objects. 
        Remarks
            For a 2D array, specify the NumberOfRows, NumberOfColumns, DistBetweenRow, and DistBetweenColumns. For creating a 3D array, specify the NumberOfLevels and DistBetweenLevels as well. 
            A rectangular array is constructed by replicating the object in the selection set the appropriate number of times. If you define one row, you must specify more than one column and vice versa. 
            The object in the selection set is assumed to be in the lower left-hand corner, and the array is generated up and to the right. If the distance between rows is a negative number, rows are added downward. If the distance between columns is a negative number, the columns are added to the left. 
            AutoCAD builds the rectangular array along a baseline defined by the current snap rotation angle. This angle is zero by default, so the rows and columns of a rectangular array are orthogonal with respect to the X and Y drawing axes. You can change this angle and create a rotated array by setting the snap rotation angle to a nonzero value. To do this, use the SnapRotationAngle property. 
            Note
                You cannot execute this method while simultaneously iterating through a collection. An iteration will open the work space for a read-only operation, while this method attempts to perform a read-write operation. Complete any iteration before you call this method. 
                AttributeReference: You should not attempt to use this method on AttributeReference objects. AttributeReference objects inherit this method because they are one of the drawing objects, however, it is not feasible to perform this operation on an attribute reference.
        """
        return self._obj.ArrayRectangular(NumberOfRows, NumberOfColumns, NumberOfLevels, DistBetweenRows, DistBetweenColumns, DistBetweenLevels)

    def Copy(self) -> AcadEntity:
        """Duplicates the given object to the same location.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        Return Value (RetVal)
            Type: All drawing objects, AttributeReference, Dimension 
            The newly created duplicate object. 
        Remarks
            AttributeReference: You should not attempt to use this method on AttributeReference objects. AttributeReference objects inherit this method because they are one of the drawing objects, however, it is not feasible to perform this operation on an attribute reference.
            Note
                You cannot execute this method while simultaneously iterating through a collection. An iteration will open the work space for a read-only operation, while this method attempts to perform a read-write operation. Complete any iteration before you call this method.
        """
        return AcadEntity(self._obj.Copy())

    def GetBoundingBox(self) -> PyGePoint3dArray:
        """Gets two points of a box enclosing the specified object.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        MinPoint 
            Access: Output-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the minimum point of the object's bounding box. 
        MaxPoint 
            Access: Output-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the maximum point of the object's bounding box. 
        Return Value (RetVal)
            No return value.
        """
        return PyGePoint3dArray(self._obj.GetBoundingBox())
    
    def Highlight(self, HighlightFlag: bool) -> None:
        """Sets the highlight status for the given object, or for all objects in a given selection set.

        object 
            Type: All drawing objects, AttributeReference, Dimension, Group, SelectionSet 
            The objects this method applies to. 
        HighlightFlag 
            Access: Input-only 
            Type: Boolean 
            True: The object is highlighted. 
            False: The existing highlight is removed from the object. 
        Return Value (RetVal)
            No return value. 
        Remarks
            Once the highlight flag for an object has been set, a call to the Update or Regen method is required to view the change. 
            Note
                This function does not return the current highlight status of an object. 
        """
        self._obj.Highlight(HighlightFlag)

    def IntersectWith(self, IntersectObject: AcadEntity | AcadAttributeReference, ExtendOption: AcExtendOption) -> PyGePoint3dArray:
        """Gets the points where one object intersects another object in the drawing.

        object 
            Type: All drawing objects (except PViewport and PolygonMesh), AttributeReference 
            The objects this method applies to. 
        IntersectObject 
            Access: Input-only 
            Type: Object 
            The object can be one of the supported drawing objects or an AttributeReference. 
        ExtendOption 
            Access: Input-only 
            Type: AcExtendOption enum 
            This option specifies if none, one or both, of the objects are to be extended in order to attempt an intersection. 
            acExtendNone: Does not extend either object. 
            acExtendThisEntity: Extends the base object. 
            acExtendOtherEntity: Extends the object passed as an argument. 
            acExtendBoth: Extends both objects. 
        Return Value (RetVal)
            Type: Variant (array of doubles) 
            The array of points where one object intersects another object in the drawing. 
        Remarks
            If the two objects do not intersect, no data is returned. You can request the point of intersection that would occur if one or both of the objects were extended to meet the other. For example, in the following illustration, Line1 is the base object from which this method was called and line3 is the object passed as a parameter. If the ExtendOption passed is acExtendThisEntity, point A is returned as the point where line1 would intersect line3 if line1 were extended. If the ExtendOption is acExtendOtherEntity, no data is returned because even if line3 were extended, it would not intersect line1.
            If the intersection type is acExtendBothEntities and line2 is passed as the parameter entity, point B is returned. If the ExtendOption is acExtendNone and line2 is the parameter entity, no data is returned. 
        """
        return self._obj.IntersectWith(IntersectObject(), ExtendOption)

    def Mirror(self, Point1: PyGePoint3d, Point2: PyGePoint3d) -> AcadEntity:
        """Creates a mirror-image copy of a planar object around an axis.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        Point1 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the first point of the mirror axis. 
        Point2 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the second point of the mirror axis. 
        Return Value (RetVal)
            Type: Object 
            This object can be one of any drawing object and is the result of mirroring the original object. 
        Remarks
            The two points specified as parameters become the endpoints of a line around which the base object is reflected. 
        """
        return self._obj.Mirror(Point1(), Point2())

    def Mirror3D(self, Point1: PyGePoint3d, Point2: PyGePoint3d, Point3: PyGePoint3d) -> AcadEntity:
        """Creates a mirror image of the given object about a plane.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        Point1 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the first point of the mirror plane. 
        Point2 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the second point of the mirror plane. 
        Point3 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the third point of the mirror plane. 
        Return Value (RetVal)
            Type: Object 
            This object can be one of any drawing object and is the result of mirroring the original object. 
        Remarks
            AutoCAD checks to see if the object to be copied owns any other object. If it does, it performs a copy on those objects as well. The process continues until all owned objects have been copied. 
            Note
                You cannot execute this method while simultaneously iterating through a collection. An iteration will open the work space for a read-only operation, while this method attempts to perform a read-write operation. Complete any iteration before you call this method. 
            AttributeReference: You should not attempt to use this method on AttributeReference objects. AttributeReference objects inherit this method because they are one of the drawing objects, however, it is not feasible to perform this operation on an attribute reference. 

        """
        return self._obj.Mirror3D(Point1(), Point2(), Point3())
    
    def Move(self, Point1: PyGePoint3d, Point2: PyGePoint3d) -> None:
        """Moves an object along a vector.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        Point1 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the first point of the move vector. 
        Point2 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the second point of the move vector. 
        Return Value (RetVal)
            No return value. 
        Remarks
            The two points you specify define a displacement vector indicating how far the given object is to be moved and in what direction. 
        """
        self._obj.Move(Point1(), Point2())

    def Rotate(self, BasePoint: PyGePoint3d, RotationAngle: float) -> None:
        """Rotates an object around a base point.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        BasePoint 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the point through which the axis of rotation is defined as parallel to the Z axis of the UCS. 
        RotationAngle 
            Access: Input-only 
            Type: Double 
            The angle in radians to rotate the object. This angle determines how far an object rotates around the base point relative to its current location. 
        No return value. 
        """
        self._obj.Rotate(BasePoint(), RotationAngle)
        
    def Rotate3D(self, Point1: PyGePoint3d, Point2: PyGePoint3d, RotationAngle: float) -> None:
        """Rotates an object around a 3D axis. Point1 and Point2 define the line that becomes the axis of rotation.

        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The object this method applies to. 
        Point1 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the first point of the axis line. 
        Point2 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the second point of the axis line. 
        RotationAngle 
            Access: Input-only 
            Type: Double 
            The angle in radians to rotate the object about the selected axis. 
        Return Value (RetVal)
            No return value. 
        """
        self._obj.Rotate3D(Point1(), Point2(), RotationAngle)
        
    def ScaleEntity(self, BasePoint: PyGePoint3d, ScaleFactor: float) -> None:
        """Scales an object equally in the X, Y, and Z directions.
        
        object 
            Type: All drawing objects, AttributeReference, Dimension 
            The objects this method applies to. 
        BasePoint 
            Access: Input-only 
            Type: Variant (three-element array of doubles) 
            The 3D WCS coordinates specifying the base point. 
        ScaleFactor 
            Access: Input-only 
            Type: Double 
            The factor by which to scale the object. The dimensions of the object are multiplied by the scale factor. A scale factor greater than 1 enlarges the object. A scale factor between 0 and 1 reduces the object. The scale factor must be greater than 0.0.
        Return Value (RetVal)
            No return value. 
        """
        self._obj.ScaleEntity(BasePoint(), ScaleFactor)
        
    def TransformBy(self, TransformationMatrix: PyGeMatrix3d) -> None:
        """Moves, scales, or rotates an object given a 4x4 transformation matrix.

        object 
            Type: All drawing objects, AttributeReference 
            The object this method applies to. 
        TransformationMatrix 
            Access: Input-only 
            Type: Variant (4x4 array of doubles) 
            A 4x4 matrix specifying the transformation to perform. 
        Return Value (RetVal)
            No return value. 
        Remarks
            The following table demonstrates the transformation matrix configuration, where R = Rotation, and T = Translation: R00 
            R00 R01 R02 T0  
            R10 R11 R12 T1  
            R20 R21 R22 T2  
            0   0   0   1  
            This method will return an error if the transformation matrix is not correct. 
            Sample transformation matrices are provided in the example code for this method. 
        """
        self._obj.TransformBy(TransformationMatrix())

    def Update(self) -> None:
        """Updates the object to the drawing screen.
        
        object 
            Type: All drawing objects, Application, AttributeReference, Dimension, SelectionSet 
            The objects this method applies to. 
        Return Value (RetVal)
            No return value. 
        Remarks
            No additional remarks.
        """
        self._obj.Update()


class AcadSubEntity(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Color: AcColor = proxy_property('AcColor','Color',AccessMode.ReadWrite)
    Hyperlinks: AcadHyperlinks = proxy_property('AcadHyperlinks','Hyperlinks',AccessMode.ReadOnly)
    Layer: str = proxy_property(str,'Layer',AccessMode.ReadWrite)
    Linetype: str = proxy_property(str,'Linetype',AccessMode.ReadWrite)
    LinetypeScale: float = proxy_property(float,'LinetypeScale',AccessMode.ReadWrite)
    Lineweight: AcLineWeight = proxy_property('AcLineWeight','Lineweight',AccessMode.ReadWrite)
    ObjectName: str = proxy_property(str,'ObjectName',AccessMode.ReadOnly)
    PlotStyleName: str = proxy_property(str,'PlotStyleName',AccessMode.ReadWrite)



# from enum import StrEnum
# class acTransparency(StrEnum):
#     ByLayer = 'ByLayer'
#     ByBlock = 'ByBlock'