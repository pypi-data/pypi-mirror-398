from __future__ import annotations
from .Base import *
from .Objects.AcadApplication import *
from .Proxy import *


class IAcadObject(AppObject):
    """The standard interface for a basic AutoCAD object."""
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    """Gets the Application object.

    object 
        Type: All objects 
        The object this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Application 
        The Application object that is the owner of the object. 
    Remarks
        The Application object represents the application's frame controls and path settings, and provides the means to navigate down the object hierarchy. 
        Release Information
        Releases: AutoCAD 2000 through AutoCAD 2017 
        This property is no longer supported for use with the FileDependency and FileDependencies objects.
    """

    Document: AcadDocument = proxy_property('AcadDocument','Document',AccessMode.ReadOnly)
    """Gets the document (drawing) in which the object belongs.

    object 
        Type: All drawing objects, Block, Blocks, Dictionary, Dictionaries, DimStyle, DimStyles, Group, Groups, Layer, Layers, Layout, Layouts, Linetype, Linetypes, ModelSpace, PaperSpace, PlotConfiguration, PlotConfigurations, RegisteredApplication, RegisteredApplications, SectionManager, SectionSettings, SortentsTable, SubDMesh, TableStyle, TextStyle, TextStyles, UCS, UCSs, View, Views, Viewport, Viewports, XRecord 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Document 
        The document (drawing) that contains the object. 
    Remarks
        No additional remarks. 
    """

    Handle: str = proxy_property(str,'Handle',AccessMode.ReadOnly)
    """Gets the handle of an object.

    object 
        Type: All drawing objects, AttributeReference, Block, Blocks, Dictionaries, Dictionary, DimStyle, DimStyles, Group, Groups, Layer, Layers, Layout, Layouts, Linetype, Linetypes, ModelSpace, PaperSpace, PlotConfiguration, PlotConfigurations, RegisteredApplication, RegisteredApplications, SectionManager, SectionSettings, SortentsTable, TableStyle, TextStyle, TextStyles, UCS, UCSs, View, Views, Viewport, Viewports, XRecord 
        The object this property applies to. 
    Property Value
        Read-only: Yes 
        Type: String 
        The handle of the entity. 
    Remarks
        An object ID and a unique handle are the two ways of referencing an object. A handle is persistent (stays the same) in a drawing for the lifetime of the object. 
        In general, use a handle unless you plan to work with certain ObjectARX functions that require an object ID. 
    """

    HasExtensionDictionary: bool = proxy_property(bool,'HasExtensionDictionary',AccessMode.ReadOnly)
    """Determines whether the object has an extension dictionary associated with it.

    object 
        Type: All drawing objects, AttributeReference, Block, Dictionary, DimStyle, Group, Layer, Layout, Linetype, Material, MLeaderStyle, PlotConfiguration, RegisteredApplication, SectionManager, SectionSettings, SortentsTable, TableStyle, TextStyle, UCS, View, Viewport, XRecord 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Boolean 
        True: The object has an extension dictionary associated with it. 
        False: The object does not have an extension dictionary associated with it. 
    Remarks
        You can create an extension dictionary for an object, or query an existing extension dictionary by using the GetExtensionDictionary method. 
    """

    ObjectName: str = proxy_property(str,'ObjectName',AccessMode.ReadOnly)
    """Gets the AutoCAD class name of the object.

    object 
        Type: All drawing objects, AttributeReference, Block, Blocks, Dictionary, Dictionaries, Dimension, DimStyle, DimStyles, Group, Groups, Layer, Layers, Layout, Layouts, Linetype, Linetypes, Material, Materials, MLeaderStyle, ModelSpace, PaperSpace, PlotConfiguration, PlotConfigurations, RegisteredApplication, RegisteredApplications, SectionManager, SectionSettings, SortentsTable, SubDMeshEdge, SubDMeshFace, SubDMeshVertex, SubEntity, SubEntSolidEdge, SubEntSolidFace, SubEntSolidNode, SubEntSolidVertex, TableStyle, TextStyle, TextStyles, UCS, UCSs, View, Views, Viewport, Viewports, XRecord 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: String 
        The AutoCAD class name of an object. 
    Remarks
        No additional remarks. 
    """

    ObjectID: int = proxy_property(int,'ObjectID',AccessMode.ReadOnly)
    """Gets the object ID.

    object 
        Type: All drawing objects, AttributeReference, Block, Blocks, Dictionary, Dictionaries, Dimension, DimStyle, DimStyles, Group, Groups, Layer, Layers, Layout, Layouts, Linetype, Linetypes, Material, Materials, MLeaderStyle, ModelSpace, PaperSpace, PlotConfiguration, PlotConfigurations, RegisteredApplication, RegisteredApplications, SectionManager, SectionSettings, SortentsTable, TableStyle, TextStyle, TextStyles, UCS, UCSs, View, Views, Viewport, Viewports, XRecord 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Long_PTR 
        The object ID of an object. 
    Remarks
        An object ID and a unique handle are both ways of referencing an object. 
        In general, use a handle unless you plan to work with certain ObjectARX functions that require an object ID. 
    """

    OwnerID: int = proxy_property(int,'OwnerID',AccessMode.ReadOnly)
    """Gets the object ID of the owner (parent) object.

    object 
        Type: All drawing objects, AttributeReference, Block, Blocks, Dictionary, Dictionaries, Dimension, DimStyle, DimStyles, Group, Groups, Layer, Layers, Layout, Layouts, Linetype, Linetypes, Material, Materials, MLeaderStyle, ModelSpace, PaperSpace, PlotConfiguration, PlotConfigurations, RegisteredApplication, RegisteredApplications, SectionManager, SectionSettings, SortentsTable, TableStyle, TextStyle, TextStyles, UCS, UCSs, View, Views, Viewport, Viewports, XRecord 
        The objects this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Long_PTR 
        The object ID of an object's owner. 
    Remarks
        No additional remarks. 
    """

    def GetExtensionDictionary(self) -> AcadDictionary: 
        """Gets the extension dictionary associated with an object.

        object 
            Type: All drawing objects, AttributeReference, Block, Dictionary, Dimension, DimStyle, Group, Layer, Layout, Linetype, Material, MLeaderStyle, PlotConfiguration, RegisteredApplication, TableStyle, TextStyle, UCS, View, Viewport, XRecord
            The objects this method applies to. 
        Return Value (RetVal)
            Type: Dictionary 
            The extension dictionary for the object. 
        Remarks
            If an object does not have an extension dictionary, this method will create a new extension dictionary for that object and return it in the return value.
            You can query an object to see if it has an extension dictionary by using the HasExtensionDictionary property. 
        """
        return AcadDictionary(self._obj.GetExtensionDictionary())

    def GetXData(self, AppName: str = '') -> tuple:
        """Gets the extended data (XData) associated with an object.

        object 
            Type: All drawing objects, AttributeReference, Block, Dictionary, Dimension, DimStyle, Group, Layer, Layout, Linetype, Material, MLeaderStyle, PlotConfiguration, RegisteredApplication, TableStyle, TextStyle, UCS, View, Viewport, XRecord
            The objects this method applies to. 
        AppName 
            Access: Input-only 
            Type: String 
            A NULL string will return all the data attached to the object, regardless of the application that created it. Supplying an application name will return only the data that was created by the specified application.
        XDataType 
            Access: Output-only 
            Type: Variant (array of shorts) 
            An array of short integer values that represent the DXF group code values for each value in the extended data (XData). 
        XDataValue 
            Access: Output-only 
            Type: Variant (array of variants) 
            An array of values that make up the extended data (XData). 
        Return Value (RetVal)
            No return value. 
        Remarks
            Extended data is an example of instance-specific data created by applications written with ObjectARX or AutoLISP. This data can be added to any object. This data follows the object's definition data, and is maintained in the order that it was saved into the document. (AutoCAD maintains this information, but does not use it.)
        """
        XDataType, XDataValue = self._obj.GetXData(AppName)
        return XDataType, XDataValue

    # def SetXData(self, XDataType: Variant, XDataValue: Variant) -> None: 
    def SetXData(self, XDataType: vShortArray, XDataValue: vVariantArray) -> None: 
        """Sets the extended data (XData) associated with an object.

        object 
            Type: All drawing objects, AttributeReference, Block, Dictionary, Dimension, DimStyle, Group, Layer, Layout, Linetype, Material, MLeaderStyle, PlotConfiguration, RegisteredApplication, TableStyle, TextStyle, UCS, View, Viewport, XRecord 
            The object this method applies to. 
        XDataType 
            Access: Input-only 
            Type: Variant (array of short) 
            An array of short integer values that represent the DXF group code values for each value in the extended data (XData). 
        XDataValue 
            Access: Input-only 
            Type: Variant (array of variants) 
            An array of values that make up the extended data (XData). 
        Return Value (RetVal)
            No return value. 
        Remarks
            Extended data is an example of instance-specific data created by applications written with ObjectARX or AutoLISP. This data can be added to any entity. This data follows the entity's definition data and is maintained in the order in which it was saved into the document. (AutoCAD maintains this information but does not use it.)
        """
        self._obj.SetXData(XDataType(), XDataValue())

class AcadObject(IAcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Delete(self) -> None: 
        """Deletes a specified object or a set of saved layer settings.

        object 
            Type: All drawing objects, AttributeReference, Block, Dictionary, DimStyle, Group, Hyperlink, Layer, LayerStateManager, Layout, Linetype, Material, MLeaderStyle, PlotConfiguration, PopupMenuItem, RegisteredApplication, SelectionSet, TableStyle, TextStyle, Toolbar, ToolbarItem, UCS, View, Viewport, XRecord 
            The objects this method applies to. 
        Return Value (RetVal)
            No return value. 
        Remarks
            When you delete an object in a collection, all remaining items in the collection are reassigned a new index based on the current count. You should therefore avoid loops that delete an object while iterating through the collection. For example, the following VBA code will result in a runtime error:
            For i = 0 To ThisDrawing.Groups.Count - 1
                ThisDrawing.Groups.Item(i).Delete
            Next I
            Instead, use the following VBA code to delete all members in a collection: 
            For Each obj In ThisDrawing.Groups
                obj.Delete
            Next obj
            You can also use the following VBA code to delete a single member of a collection: 
            ThisDrawing.Groups.Item("group1").DeleteAn error will result if you attempt to delete a collection object. 
            ToolbarItem: You can only add or remove toolbar items when the toolbar is visible. 
            LayerStateManager: This object takes an argument, Name, which is a string representing the layer state to be deleted.
        """
        self._obj.Delete()

class IAcadObjectCollection(IAcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    """Gets the number of items in the object.

    object 
        Type: All Collections, Block, Dictionary, Group, Materials, SectionManager, SelectionSet 
        The object this property applies to. 
    Property Value
        Read-only: Yes 
        Type: Integer 
        The number of items in the object. 
    Remarks
        No additional remarks. 
    Release Information
        Releases: AutoCAD 2000 through AutoCAD 2017 
        This property is no longer supported for use with the FileDependencies object.
    """

    def Item(self, Index: int | str):
        obj = self._obj.Item(Index)
        return AcadObject(obj)

    def __iter__(self):
        for item in self._obj:
            yield AcadObject(item)