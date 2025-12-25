from enum import Enum, IntEnum, StrEnum

class Ac3DPolylineType(IntEnum):
    acCubicSpline3DPoly           =2          # from enum Ac3DPolylineType
    acQuadSpline3DPoly            =1          # from enum Ac3DPolylineType
    acSimple3DPoly                =0          # from enum Ac3DPolylineType

class AcARXDemandLoad(IntEnum):
    acDemanLoadDisable            =0          # from enum AcARXDemandLoad
    acDemandLoadCmdInvoke         =2          # from enum AcARXDemandLoad
    acDemandLoadOnObjectDetect    =1          # from enum AcARXDemandLoad

class AcActiveSpace(IntEnum):
    acModelSpace                  =1          # from enum AcActiveSpace
    acPaperSpace                  =0          # from enum AcActiveSpace

class AcAlignment(IntEnum):
    acAlignmentAligned            =3          # from enum AcAlignment
    acAlignmentBottomCenter       =13         # from enum AcAlignment
    acAlignmentBottomLeft         =12         # from enum AcAlignment
    acAlignmentBottomRight        =14         # from enum AcAlignment
    acAlignmentCenter             =1          # from enum AcAlignment
    acAlignmentFit                =5          # from enum AcAlignment
    acAlignmentLeft               =0          # from enum AcAlignment
    acAlignmentMiddle             =4          # from enum AcAlignment
    acAlignmentMiddleCenter       =10         # from enum AcAlignment
    acAlignmentMiddleLeft         =9          # from enum AcAlignment
    acAlignmentMiddleRight        =11         # from enum AcAlignment
    acAlignmentRight              =2          # from enum AcAlignment
    acAlignmentTopCenter          =7          # from enum AcAlignment
    acAlignmentTopLeft            =6          # from enum AcAlignment
    acAlignmentTopRight           =8          # from enum AcAlignment

class AcAlignmentPointAcquisition(IntEnum):
	'''
	Захват точек отслеживания
	'''
	acAlignPntAcquisitionAutomatic=0          # from enum AcAlignmentPointAcquisition
	acAlignPntAcquisitionShiftToAcquire=1          # from enum AcAlignmentPointAcquisition

class AcAngleUnits(IntEnum):
	acDegreeMinuteSeconds         =1          # from enum AcAngleUnits
	acDegrees                     =0          # from enum AcAngleUnits
	acGrads                       =2          # from enum AcAngleUnits
	acRadians                     =3          # from enum AcAngleUnits

class AcAttachmentPoint(IntEnum):
	acAttachmentPointBottomCenter =8          # from enum AcAttachmentPoint
	acAttachmentPointBottomLeft   =7          # from enum AcAttachmentPoint
	acAttachmentPointBottomRight  =9          # from enum AcAttachmentPoint
	acAttachmentPointMiddleCenter =5          # from enum AcAttachmentPoint
	acAttachmentPointMiddleLeft   =4          # from enum AcAttachmentPoint
	acAttachmentPointMiddleRight  =6          # from enum AcAttachmentPoint
	acAttachmentPointTopCenter    =2          # from enum AcAttachmentPoint
	acAttachmentPointTopLeft      =1          # from enum AcAttachmentPoint
	acAttachmentPointTopRight     =3          # from enum AcAttachmentPoint
     
class AcAttributeMode(IntEnum):
	acAttributeModeConstant       =2          # from enum AcAttributeMode
	acAttributeModeInvisible      =1          # from enum AcAttributeMode
	acAttributeModeLockPosition   =16         # from enum AcAttributeMode
	acAttributeModeMultipleLine   =32         # from enum AcAttributeMode
	acAttributeModeNormal         =0          # from enum AcAttributeMode
	acAttributeModePreset         =8          # from enum AcAttributeMode
	acAttributeModeVerify         =4          # from enum AcAttributeMode

class AcBlockConnectionType(IntEnum):
	acConnectBase                 =1          # from enum AcBlockConnectionType
	acConnectExtents              =0          # from enum AcBlockConnectionType

class AcBlockScaling(IntEnum):
	acAny                         =0          # from enum AcBlockScaling
	acUniform                     =1          # from enum AcBlockScaling

class AcBoolean(IntEnum):
	acFalse                       =0          # from enum AcBoolean
	acTrue                        =1          # from enum AcBoolean

class AcBooleanType(IntEnum):
	acIntersection                =1          # from enum AcBooleanType
	acSubtraction                 =2          # from enum AcBooleanType
	acUnion                       =0          # from enum AcBooleanType

class AcCellAlignment(IntEnum):
	acBottomCenter                =8          # from enum AcCellAlignment
	acBottomLeft                  =7          # from enum AcCellAlignment
	acBottomRight                 =9          # from enum AcCellAlignment
	acMiddleCenter                =5          # from enum AcCellAlignment
	acMiddleLeft                  =4          # from enum AcCellAlignment
	acMiddleRight                 =6          # from enum AcCellAlignment
	acTopCenter                   =2          # from enum AcCellAlignment
	acTopLeft                     =1          # from enum AcCellAlignment
	acTopRight                    =3          # from enum AcCellAlignment

class AcCellContentLayout(IntEnum):
	acCellContentLayoutFlow       =1          # from enum AcCellContentLayout
	acCellContentLayoutStackedHorizontal=2          # from enum AcCellContentLayout
	acCellContentLayoutStackedVertical=4          # from enum AcCellContentLayout

class AcCellContentType(IntEnum):
	acCellContentTypeBlock        =4          # from enum AcCellContentType
	acCellContentTypeField        =2          # from enum AcCellContentType
	acCellContentTypeUnknown      =0          # from enum AcCellContentType
	acCellContentTypeValue        =1          # from enum AcCellContentType

class AcCellEdgeMask(IntEnum):
	acBottomMask                  =4          # from enum AcCellEdgeMask
	acLeftMask                    =8          # from enum AcCellEdgeMask
	acRightMask                   =2          # from enum AcCellEdgeMask
	acTopMask                     =1          # from enum AcCellEdgeMask

class AcCellMargin(IntEnum):
	acCellMarginBottom            =4          # from enum AcCellMargin
	acCellMarginHorzSpacing       =16         # from enum AcCellMargin
	acCellMarginLeft              =2          # from enum AcCellMargin
	acCellMarginRight             =8          # from enum AcCellMargin
	acCellMarginTop               =1          # from enum AcCellMargin
	acCellMarginVertSpacing       =32         # from enum AcCellMargin

class AcCellOption(IntEnum):
	kCellOptionNone               =0          # from enum AcCellOption
	kInheritCellFormat            =1          # from enum AcCellOption

class AcCellProperty(IntEnum):
	acAlignmentProperty           =32         # from enum AcCellProperty
	acAllCellProperties           =524287     # from enum AcCellProperty
	acAutoScale                   =32768      # from enum AcCellProperty
	acBackgroundColor             =128        # from enum AcCellProperty
	acBitProperties               =245760     # from enum AcCellProperty
	acContentColor                =64         # from enum AcCellProperty
	acContentLayout               =262144     # from enum AcCellProperty
	acContentProperties           =33662      # from enum AcCellProperty
	acDataFormat                  =4          # from enum AcCellProperty
	acDataType                    =2          # from enum AcCellProperty
	acDataTypeAndFormat           =6          # from enum AcCellProperty
	acEnableBackgroundColor       =16384      # from enum AcCellProperty
	acFlowDirBtoT                 =131072     # from enum AcCellProperty
	acInvalidCellProperty         =0          # from enum AcCellProperty
	acLock                        =1          # from enum AcCellProperty
	acMarginBottom                =8192       # from enum AcCellProperty
	acMarginLeft                  =1024       # from enum AcCellProperty
	acMarginRight                 =4096       # from enum AcCellProperty
	acMarginTop                   =2048       # from enum AcCellProperty
	acMergeAll                    =65536      # from enum AcCellProperty
	acRotation                    =8          # from enum AcCellProperty
	acScale                       =16         # from enum AcCellProperty
	acTextHeight                  =512        # from enum AcCellProperty
	acTextStyle                   =256        # from enum AcCellProperty

class AcCellState(IntEnum):
	acCellStateContentLocked      =1          # from enum AcCellState
	acCellStateContentModified    =32         # from enum AcCellState
	acCellStateContentReadOnly    =2          # from enum AcCellState
	acCellStateFormatLocked       =4          # from enum AcCellState
	acCellStateFormatModified     =64         # from enum AcCellState
	acCellStateFormatReadOnly     =8          # from enum AcCellState
	acCellStateLinked             =16         # from enum AcCellState
	acCellStateNone               =0          # from enum AcCellState

class AcCellType(IntEnum):
	acBlockCell                   =2          # from enum AcCellType
	acTextCell                    =1          # from enum AcCellType
	acUnknownCell                 =0          # from enum AcCellType

class AcColor(IntEnum):
	_ignore_ = ('v','attr_name')
	acByBlock   = 0
	acByLayer   = 256
	acRed       = 1
	acYellow    = 2
	acGreen     = 3
	acCyan      = 4
	acBlue      = 5
	acMagenta   = 6
	acWhite     = 7
	for v in range(8, 256):
		attr_name = f"color_{v}"
		locals()[attr_name] = v


class AcColorMethod(IntEnum):
	acColorMethodByACI            =195        # from enum AcColorMethod
	acColorMethodByBlock          =193        # from enum AcColorMethod
	acColorMethodByLayer          =192        # from enum AcColorMethod
	acColorMethodByRGB            =194        # from enum AcColorMethod
	acColorMethodForeground       =197        # from enum AcColorMethod

class AcCoordinateSystem(IntEnum):
	acDisplayDCS                  =2          # from enum AcCoordinateSystem
	acOCS                         =4          # from enum AcCoordinateSystem
	acPaperSpaceDCS               =3          # from enum AcCoordinateSystem
	acUCS                         =1          # from enum AcCoordinateSystem
	acWorld                       =0          # from enum AcCoordinateSystem

class AcDataLinkUpdateDirection(IntEnum):
	acUpdateDataFromSource        =1          # from enum AcDataLinkUpdateDirection
	acUpdateSourceFromData        =2          # from enum AcDataLinkUpdateDirection

class AcDataLinkUpdateOption(IntEnum):
	acUpdateOptionIncludeXrefs    =1048576    # from enum AcDataLinkUpdateOption
	acUpdateOptionNone            =0          # from enum AcDataLinkUpdateOption
	acUpdateOptionOverwriteContentModifiedAfterUpdate=131072     # from enum AcDataLinkUpdateOption
	acUpdateOptionOverwriteFormatModifiedAfterUpdate=262144     # from enum AcDataLinkUpdateOption
	acUpdateOptionUpdateFullSourceRange=524288     # from enum AcDataLinkUpdateOption

class AcDimArcLengthSymbol(IntEnum):
	acSymAbove                    =1          # from enum AcDimArcLengthSymbol
	acSymInFront                  =0          # from enum AcDimArcLengthSymbol
	acSymNone                     =2          # from enum AcDimArcLengthSymbol

class AcDimArrowheadType(IntEnum):
	acArrowArchTick               =4          # from enum AcDimArrowheadType
	acArrowBoxBlank               =14         # from enum AcDimArrowheadType
	acArrowBoxFilled              =15         # from enum AcDimArrowheadType
	acArrowClosed                 =2          # from enum AcDimArrowheadType
	acArrowClosedBlank            =1          # from enum AcDimArrowheadType
	acArrowDatumBlank             =16         # from enum AcDimArrowheadType
	acArrowDatumFilled            =17         # from enum AcDimArrowheadType
	acArrowDefault                =0          # from enum AcDimArrowheadType
	acArrowDot                    =3          # from enum AcDimArrowheadType
	acArrowDotBlank               =12         # from enum AcDimArrowheadType
	acArrowDotSmall               =11         # from enum AcDimArrowheadType
	acArrowIntegral               =18         # from enum AcDimArrowheadType
	acArrowNone                   =19         # from enum AcDimArrowheadType
	acArrowOblique                =5          # from enum AcDimArrowheadType
	acArrowOpen                   =6          # from enum AcDimArrowheadType
	acArrowOpen30                 =10         # from enum AcDimArrowheadType
	acArrowOpen90                 =9          # from enum AcDimArrowheadType
	acArrowOrigin                 =7          # from enum AcDimArrowheadType
	acArrowOrigin2                =8          # from enum AcDimArrowheadType
	acArrowSmall                  =13         # from enum AcDimArrowheadType
	acArrowUserDefined            =20         # from enum AcDimArrowheadType

class AcDimCenterType(IntEnum):
	acCenterLine                  =1          # from enum AcDimCenterType
	acCenterMark                  =0          # from enum AcDimCenterType
	acCenterNone                  =2          # from enum AcDimCenterType

class AcDimFit(IntEnum):
	acArrowsOnly                  =1          # from enum AcDimFit
	acBestFit                     =3          # from enum AcDimFit
	acTextAndArrows               =0          # from enum AcDimFit
	acTextOnly                    =2          # from enum AcDimFit

class AcDimFractionType(IntEnum):
	acDiagonal                    =1          # from enum AcDimFractionType
	acHorizontal                  =0          # from enum AcDimFractionType
	acNotStacked                  =2          # from enum AcDimFractionType

class AcDimHorizontalJustification(IntEnum):
	acFirstExtensionLine          =1          # from enum AcDimHorizontalJustification
	acHorzCentered                =0          # from enum AcDimHorizontalJustification
	acOverFirstExtension          =3          # from enum AcDimHorizontalJustification
	acOverSecondExtension         =4          # from enum AcDimHorizontalJustification
	acSecondExtensionLine         =2          # from enum AcDimHorizontalJustification

class AcDimLUnits(IntEnum):
	acDimLArchitectural           =4          # from enum AcDimLUnits
	acDimLDecimal                 =2          # from enum AcDimLUnits
	acDimLEngineering             =3          # from enum AcDimLUnits
	acDimLFractional              =5          # from enum AcDimLUnits
	acDimLScientific              =1          # from enum AcDimLUnits
	acDimLWindowsDesktop          =6          # from enum AcDimLUnits

class AcDimPrecision(IntEnum):
	acDimPrecisionEight           =8          # from enum AcDimPrecision
	acDimPrecisionFive            =5          # from enum AcDimPrecision
	acDimPrecisionFour            =4          # from enum AcDimPrecision
	acDimPrecisionOne             =1          # from enum AcDimPrecision
	acDimPrecisionSeven           =7          # from enum AcDimPrecision
	acDimPrecisionSix             =6          # from enum AcDimPrecision
	acDimPrecisionThree           =3          # from enum AcDimPrecision
	acDimPrecisionTwo             =2          # from enum AcDimPrecision
	acDimPrecisionZero            =0          # from enum AcDimPrecision

class AcDimTextMovement(IntEnum):
	acDimLineWithText             =0          # from enum AcDimTextMovement
	acMoveTextAddLeader           =1          # from enum AcDimTextMovement
	acMoveTextNoLeader            =2          # from enum AcDimTextMovement

class AcDimToleranceJustify(IntEnum):
	acTolBottom                   =0          # from enum AcDimToleranceJustify
	acTolMiddle                   =1          # from enum AcDimToleranceJustify
	acTolTop                      =2          # from enum AcDimToleranceJustify

class AcDimToleranceMethod(IntEnum):
	acTolBasic                    =4          # from enum AcDimToleranceMethod
	acTolDeviation                =2          # from enum AcDimToleranceMethod
	acTolLimits                   =3          # from enum AcDimToleranceMethod
	acTolNone                     =0          # from enum AcDimToleranceMethod
	acTolSymmetrical              =1          # from enum AcDimToleranceMethod

class AcDimUnits(IntEnum):
	acDimArchitectural            =6          # from enum AcDimUnits
	acDimArchitecturalStacked     =4          # from enum AcDimUnits
	acDimDecimal                  =2          # from enum AcDimUnits
	acDimEngineering              =3          # from enum AcDimUnits
	acDimFractional               =7          # from enum AcDimUnits
	acDimFractionalStacked        =5          # from enum AcDimUnits
	acDimScientific               =1          # from enum AcDimUnits
	acDimWindowsDesktop           =8          # from enum AcDimUnits

class AcDimVerticalJustification(IntEnum):
	acAbove                       =1          # from enum AcDimVerticalJustification
	acJIS                         =3          # from enum AcDimVerticalJustification
	acOutside                     =2          # from enum AcDimVerticalJustification
	acUnder                       =4          # from enum AcDimVerticalJustification
	acVertCentered                =0          # from enum AcDimVerticalJustification

class AcDragDisplayMode(IntEnum):
	acDragDisplayAutomatically    =2          # from enum AcDragDisplayMode
	acDragDisplayOnRequest        =1          # from enum AcDragDisplayMode
	acDragDoNotDisplay            =0          # from enum AcDragDisplayMode

class AcDrawLeaderOrderType(IntEnum):
	acDrawLeaderHeadFirst         =0          # from enum AcDrawLeaderOrderType
	acDrawLeaderTailFirst         =1          # from enum AcDrawLeaderOrderType

class AcDrawMLeaderOrderType(IntEnum):
	acDrawContentFirst            =0          # from enum AcDrawMLeaderOrderType
	acDrawLeaderFirst             =1          # from enum AcDrawMLeaderOrderType

class AcDrawingAreaSCMCommand(IntEnum):
	acEnableSCM                   =2          # from enum AcDrawingAreaSCMCommand
	acEnableSCMOptions            =1          # from enum AcDrawingAreaSCMCommand
	acEnter                       =0          # from enum AcDrawingAreaSCMCommand

class AcDrawingAreaSCMDefault(IntEnum):
	acRepeatLastCommand           =0          # from enum AcDrawingAreaSCMDefault
	acSCM                         =1          # from enum AcDrawingAreaSCMDefault

class AcDrawingAreaSCMEdit(IntEnum):
	acEdRepeatLastCommand         =0          # from enum AcDrawingAreaSCMEdit
	acEdSCM                       =1          # from enum AcDrawingAreaSCMEdit

class AcDrawingAreaShortCutMenu(IntEnum):
	acNoDrawingAreaShortCutMenu   =0          # from enum AcDrawingAreaShortCutMenu
	acUseDefaultDrawingAreaShortCutMenu=1          # from enum AcDrawingAreaShortCutMenu

class AcDrawingDirection(IntEnum):
	acBottomToTop                 =4          # from enum AcDrawingDirection
	acByStyle                     =5          # from enum AcDrawingDirection
	acLeftToRight                 =1          # from enum AcDrawingDirection
	acRightToLeft                 =2          # from enum AcDrawingDirection
	acTopToBottom                 =3          # from enum AcDrawingDirection

class AcDynamicBlockReferencePropertyUnitsType(IntEnum):
	acAngular                     =1          # from enum AcDynamicBlockReferencePropertyUnitsType
	acArea                        =3          # from enum AcDynamicBlockReferencePropertyUnitsType
	acDistance                    =2          # from enum AcDynamicBlockReferencePropertyUnitsType
	acNoUnits                     =0          # from enum AcDynamicBlockReferencePropertyUnitsType

class AcEntityName(IntEnum):
	ac3dFace                      =1          # from enum AcEntityName
	ac3dPolyline                  =2          # from enum AcEntityName
	ac3dSolid                     =3          # from enum AcEntityName
	acArc                         =4          # from enum AcEntityName
	acAttribute                   =5          # from enum AcEntityName
	acAttributeReference          =6          # from enum AcEntityName
	acBlockReference              =7          # from enum AcEntityName
	acCircle                      =8          # from enum AcEntityName
	acDgnUnderlay                 =47         # from enum AcEntityName
	acDim3PointAngular            =41         # from enum AcEntityName
	acDimAligned                  =9          # from enum AcEntityName
	acDimAngular                  =10         # from enum AcEntityName
	acDimArcLength                =44         # from enum AcEntityName
	acDimDiametric                =12         # from enum AcEntityName
	acDimOrdinate                 =13         # from enum AcEntityName
	acDimRadial                   =14         # from enum AcEntityName
	acDimRadialLarge              =45         # from enum AcEntityName
	acDimRotated                  =15         # from enum AcEntityName
	acDwfUnderlay                 =46         # from enum AcEntityName
	acEllipse                     =16         # from enum AcEntityName
	acExternalReference           =42         # from enum AcEntityName
	acGroup                       =37         # from enum AcEntityName
	acHatch                       =17         # from enum AcEntityName
	acLeader                      =18         # from enum AcEntityName
	acLine                        =19         # from enum AcEntityName
	acMInsertBlock                =38         # from enum AcEntityName
	acMLeader                     =48         # from enum AcEntityName
	acMLine                       =40         # from enum AcEntityName
	acMtext                       =21         # from enum AcEntityName
	acNurbSurface                 =51         # from enum AcEntityName
	acPViewport                   =35         # from enum AcEntityName
	acPdfUnderlay                 =50         # from enum AcEntityName
	acPoint                       =22         # from enum AcEntityName
	acPolyfaceMesh                =39         # from enum AcEntityName
	acPolyline                    =23         # from enum AcEntityName
	acPolylineLight               =24         # from enum AcEntityName
	acPolymesh                    =25         # from enum AcEntityName
	acRaster                      =26         # from enum AcEntityName
	acRay                         =27         # from enum AcEntityName
	acRegion                      =28         # from enum AcEntityName
	acShape                       =29         # from enum AcEntityName
	acSolid                       =30         # from enum AcEntityName
	acSpline                      =31         # from enum AcEntityName
	acSubDMesh                    =49         # from enum AcEntityName
	acTable                       =43         # from enum AcEntityName
	acText                        =32         # from enum AcEntityName
	acTolerance                   =33         # from enum AcEntityName
	acTrace                       =34         # from enum AcEntityName
	acXline                       =36         # from enum AcEntityName

class AcExtendOption(IntEnum):
	acExtendBoth                  =3          # from enum AcExtendOption
	acExtendNone                  =0          # from enum AcExtendOption
	acExtendOtherEntity           =2          # from enum AcExtendOption
	acExtendThisEntity            =1          # from enum AcExtendOption

class AcFormatOption(IntEnum):
	acForEditing                  =1          # from enum AcFormatOption
	acForExpression               =2          # from enum AcFormatOption
	acIgnoreMtextFormat           =8          # from enum AcFormatOption
	acUseMaximumPrecision         =4          # from enum AcFormatOption
	kFormatOptionNone             =0          # from enum AcFormatOption

class AcGradientPatternType(IntEnum):
	acPreDefinedGradient          =0          # from enum AcGradientPatternType
	acUserDefinedGradient         =1          # from enum AcGradientPatternType

class AcGridLineStyle(IntEnum):
	acGridLineStyleDouble         =2          # from enum AcGridLineStyle
	acGridLineStyleSingle         =1          # from enum AcGridLineStyle

class AcGridLineType(IntEnum):
	acHorzBottom                  =4          # from enum AcGridLineType
	acHorzInside                  =2          # from enum AcGridLineType
	acHorzTop                     =1          # from enum AcGridLineType
	acInvalidGridLine             =0          # from enum AcGridLineType
	acVertInside                  =16         # from enum AcGridLineType
	acVertLeft                    =8          # from enum AcGridLineType
	acVertRight                   =32         # from enum AcGridLineType

class AcHatchObjectType(IntEnum):
	acGradientObject              =1          # from enum AcHatchObjectType
	acHatchObject                 =0          # from enum AcHatchObjectType

class AcHatchStyle(IntEnum):
	acHatchStyleIgnore            =2          # from enum AcHatchStyle
	acHatchStyleNormal            =0          # from enum AcHatchStyle
	acHatchStyleOuter             =1          # from enum AcHatchStyle

class AcHelixConstrainType(IntEnum):
	acHeight                      =2          # from enum AcHelixConstrainType
	acTurnHeight                  =0          # from enum AcHelixConstrainType
	acTurns                       =1          # from enum AcHelixConstrainType

class AcHelixTwistType(IntEnum):
	acCCW                         =0          # from enum AcHelixTwistType
	acCW                          =1          # from enum AcHelixTwistType

class AcHorizontalAlignment(IntEnum):
	acHorizontalAlignmentAligned  =3          # from enum AcHorizontalAlignment
	acHorizontalAlignmentCenter   =1          # from enum AcHorizontalAlignment
	acHorizontalAlignmentFit      =5          # from enum AcHorizontalAlignment
	acHorizontalAlignmentLeft     =0          # from enum AcHorizontalAlignment
	acHorizontalAlignmentMiddle   =4          # from enum AcHorizontalAlignment
	acHorizontalAlignmentRight    =2          # from enum AcHorizontalAlignment

class AcISOPenWidth(IntEnum):
	acPenWidth013                 =13         # from enum AcISOPenWidth
	acPenWidth018                 =18         # from enum AcISOPenWidth
	acPenWidth025                 =25         # from enum AcISOPenWidth
	acPenWidth035                 =35         # from enum AcISOPenWidth
	acPenWidth050                 =50         # from enum AcISOPenWidth
	acPenWidth070                 =70         # from enum AcISOPenWidth
	acPenWidth100                 =100        # from enum AcISOPenWidth
	acPenWidth140                 =140        # from enum AcISOPenWidth
	acPenWidth200                 =200        # from enum AcISOPenWidth
	acPenWidthUnk                 =-1         # from enum AcISOPenWidth

class AcInsertUnits(IntEnum):
	acInsertUnitsAngstroms        =11         # from enum AcInsertUnits
	acInsertUnitsAstronomicalUnits=18         # from enum AcInsertUnits
	acInsertUnitsCentimeters      =5          # from enum AcInsertUnits
	acInsertUnitsDecameters       =15         # from enum AcInsertUnits
	acInsertUnitsDecimeters       =14         # from enum AcInsertUnits
	acInsertUnitsFeet             =2          # from enum AcInsertUnits
	acInsertUnitsGigameters       =17         # from enum AcInsertUnits
	acInsertUnitsHectometers      =16         # from enum AcInsertUnits
	acInsertUnitsInches           =1          # from enum AcInsertUnits
	acInsertUnitsKilometers       =7          # from enum AcInsertUnits
	acInsertUnitsLightYears       =19         # from enum AcInsertUnits
	acInsertUnitsMeters           =6          # from enum AcInsertUnits
	acInsertUnitsMicroinches      =8          # from enum AcInsertUnits
	acInsertUnitsMicrons          =13         # from enum AcInsertUnits
	acInsertUnitsMiles            =3          # from enum AcInsertUnits
	acInsertUnitsMillimeters      =4          # from enum AcInsertUnits
	acInsertUnitsMils             =9          # from enum AcInsertUnits
	acInsertUnitsNanometers       =12         # from enum AcInsertUnits
	acInsertUnitsParsecs          =20         # from enum AcInsertUnits
	acInsertUnitsUSSurveyFeet     =21         # from enum AcInsertUnits
	acInsertUnitsUSSurveyInch     =22         # from enum AcInsertUnits
	acInsertUnitsUSSurveyMile     =24         # from enum AcInsertUnits
	acInsertUnitsUSSurveyYard     =23         # from enum AcInsertUnits
	acInsertUnitsUnitless         =0          # from enum AcInsertUnits
	acInsertUnitsYards            =10         # from enum AcInsertUnits

class AcInsertUnitsAction(IntEnum):
	acInsertUnitsAutoAssign       =1          # from enum AcInsertUnitsAction
	acInsertUnitsPrompt           =0          # from enum AcInsertUnitsAction

class AcKeyboardAccelerator(IntEnum):
	acPreferenceClassic           =0          # from enum AcKeyboardAccelerator
	acPreferenceCustom            =1          # from enum AcKeyboardAccelerator

class AcKeyboardPriority(IntEnum):
	acKeyboardEntry               =1          # from enum AcKeyboardPriority
	acKeyboardEntryExceptScripts  =2          # from enum AcKeyboardPriority
	acKeyboardRunningObjSnap      =0          # from enum AcKeyboardPriority

class AcLayerStateMask(IntEnum):
	acLsAll                       =65535      # from enum AcLayerStateMask
	acLsColor                     =32         # from enum AcLayerStateMask
	acLsFrozen                    =2          # from enum AcLayerStateMask
	acLsLineType                  =64         # from enum AcLayerStateMask
	acLsLineWeight                =128        # from enum AcLayerStateMask
	acLsLocked                    =4          # from enum AcLayerStateMask
	acLsNewViewport               =16         # from enum AcLayerStateMask
	acLsNone                      =0          # from enum AcLayerStateMask
	acLsOn                        =1          # from enum AcLayerStateMask
	acLsPlot                      =8          # from enum AcLayerStateMask
	acLsPlotStyle                 =256        # from enum AcLayerStateMask

class AcLeaderType(IntEnum):
	acLineNoArrow                 =0          # from enum AcLeaderType
	acLineWithArrow               =2          # from enum AcLeaderType
	acSplineNoArrow               =1          # from enum AcLeaderType
	acSplineWithArrow             =3          # from enum AcLeaderType

class AcLineSpacingStyle(IntEnum):
	acLineSpacingStyleAtLeast     =1          # from enum AcLineSpacingStyle
	acLineSpacingStyleExactly     =2          # from enum AcLineSpacingStyle

class AcLineWeight(IntEnum):
	acLnWt000                     =0          # from enum AcLineWeight
	acLnWt005                     =5          # from enum AcLineWeight
	acLnWt009                     =9          # from enum AcLineWeight
	acLnWt013                     =13         # from enum AcLineWeight
	acLnWt015                     =15         # from enum AcLineWeight
	acLnWt018                     =18         # from enum AcLineWeight
	acLnWt020                     =20         # from enum AcLineWeight
	acLnWt025                     =25         # from enum AcLineWeight
	acLnWt030                     =30         # from enum AcLineWeight
	acLnWt035                     =35         # from enum AcLineWeight
	acLnWt040                     =40         # from enum AcLineWeight
	acLnWt050                     =50         # from enum AcLineWeight
	acLnWt053                     =53         # from enum AcLineWeight
	acLnWt060                     =60         # from enum AcLineWeight
	acLnWt070                     =70         # from enum AcLineWeight
	acLnWt080                     =80         # from enum AcLineWeight
	acLnWt090                     =90         # from enum AcLineWeight
	acLnWt100                     =100        # from enum AcLineWeight
	acLnWt106                     =106        # from enum AcLineWeight
	acLnWt120                     =120        # from enum AcLineWeight
	acLnWt140                     =140        # from enum AcLineWeight
	acLnWt158                     =158        # from enum AcLineWeight
	acLnWt200                     =200        # from enum AcLineWeight
	acLnWt211                     =211        # from enum AcLineWeight
	acLnWtByBlock                 =-2         # from enum AcLineWeight
	acLnWtByLayer                 =-1         # from enum AcLineWeight
	acLnWtByLwDefault             =-3         # from enum AcLineWeight

class AcLoadPalette(IntEnum):
	acPaletteByDrawing            =0          # from enum AcLoadPalette
	acPaletteBySession            =1          # from enum AcLoadPalette

class AcLoftedSurfaceNormalType(IntEnum):
	acAllNormal                   =5          # from enum AcLoftedSurfaceNormalType
	acEndsNormal                  =4          # from enum AcLoftedSurfaceNormalType
	acFirstNormal                 =2          # from enum AcLoftedSurfaceNormalType
	acLastNormal                  =3          # from enum AcLoftedSurfaceNormalType
	acRuled                       =0          # from enum AcLoftedSurfaceNormalType
	acSmooth                      =1          # from enum AcLoftedSurfaceNormalType
	acUseDraftAngles              =6          # from enum AcLoftedSurfaceNormalType

class AcLoopType(IntEnum):
	acHatchLoopTypeDefault        =0          # from enum AcLoopType
	acHatchLoopTypeDerived        =4          # from enum AcLoopType
	acHatchLoopTypeExternal       =1          # from enum AcLoopType
	acHatchLoopTypePolyline       =2          # from enum AcLoopType
	acHatchLoopTypeTextbox        =8          # from enum AcLoopType

class AcMLeaderContentType(IntEnum):
	acBlockContent                =1          # from enum AcMLeaderContentType
	acMTextContent                =2          # from enum AcMLeaderContentType
	acNoneContent                 =0          # from enum AcMLeaderContentType

class AcMLeaderType(IntEnum):
	acInVisibleLeader             =0          # from enum AcMLeaderType
	acSplineLeader                =2          # from enum AcMLeaderType
	acStraightLeader              =1          # from enum AcMLeaderType

class AcMLineJustification(IntEnum):
	acBottom                      =2          # from enum AcMLineJustification
	acTop                         =0          # from enum AcMLineJustification
	acZero                        =1          # from enum AcMLineJustification

class AcMeasurementUnits(IntEnum):
	acEnglish                     =0          # from enum AcMeasurementUnits
	acMetric                      =1          # from enum AcMeasurementUnits

class AcMenuFileType(IntEnum):
	acMenuFileCompiled            =0          # from enum AcMenuFileType
	acMenuFileSource              =1          # from enum AcMenuFileType

class AcMenuGroupType(IntEnum):
	acBaseMenuGroup               =0          # from enum AcMenuGroupType
	acPartialMenuGroup            =1          # from enum AcMenuGroupType

class AcMenuItemType(IntEnum):
	acMenuItem                    =0          # from enum AcMenuItemType
	acMenuSeparator               =1          # from enum AcMenuItemType
	acMenuSubMenu                 =2          # from enum AcMenuItemType

class AcMergeCellStyleOption(IntEnum):
	acMergeCellStyleConvertDuplicatesToOverrides=4          # from enum AcMergeCellStyleOption
	acMergeCellStyleCopyDuplicates=1          # from enum AcMergeCellStyleOption
	acMergeCellStyleIgnoreNewStyles=8          # from enum AcMergeCellStyleOption
	acMergeCellStyleNone          =0          # from enum AcMergeCellStyleOption
	acMergeCellStyleOverwriteDuplicates=2          # from enum AcMergeCellStyleOption

class AcMeshCreaseType(IntEnum):
	acAlwaysCrease                =1          # from enum AcMeshCreaseType
	acCreaseByLevel               =2          # from enum AcMeshCreaseType
	acNoneCrease                  =0          # from enum AcMeshCreaseType

class AcOlePlotQuality(IntEnum):
	acOPQHighGraphics             =2          # from enum AcOlePlotQuality
	acOPQLowGraphics              =1          # from enum AcOlePlotQuality
	acOPQMonochrome               =0          # from enum AcOlePlotQuality

class AcOleQuality(IntEnum):
	acOQGraphics                  =2          # from enum AcOleQuality
	acOQHighPhoto                 =4          # from enum AcOleQuality
	acOQLineArt                   =0          # from enum AcOleQuality
	acOQPhoto                     =3          # from enum AcOleQuality
	acOQText                      =1          # from enum AcOleQuality

class AcOleType(IntEnum):
	acOTEmbedded                  =2          # from enum AcOleType
	acOTLink                      =1          # from enum AcOleType
	acOTStatic                    =3          # from enum AcOleType

class AcOnOff(IntEnum):
	acOff                         =0          # from enum AcOnOff
	acOn                          =1          # from enum AcOnOff

class AcParseOption(IntEnum):
	acParseOptionNone             =0          # from enum AcParseOption
	acPreserveMtextFormat         =2          # from enum AcParseOption
	acSetDefaultFormat            =1          # from enum AcParseOption

class AcPatternType(IntEnum):
	acHatchPatternTypeCustomDefined=2          # from enum AcPatternType
	acHatchPatternTypePreDefined  =1          # from enum AcPatternType
	acHatchPatternTypeUserDefined =0          # from enum AcPatternType

class AcPlotOrientation(IntEnum):
	acPlotOrientationLandscape    =1          # from enum AcPlotOrientation
	acPlotOrientationPortrait     =0          # from enum AcPlotOrientation

class AcPlotPaperUnits(IntEnum):
	acInches                      =0          # from enum AcPlotPaperUnits
	acMillimeters                 =1          # from enum AcPlotPaperUnits
	acPixels                      =2          # from enum AcPlotPaperUnits

class AcPlotPolicy(IntEnum):
	acPolicyLegacy                =1          # from enum AcPlotPolicy
	acPolicyNamed                 =0          # from enum AcPlotPolicy

class AcPlotPolicyForLegacyDwgs(IntEnum):
	acPolicyLegacyDefault         =0          # from enum AcPlotPolicyForLegacyDwgs
	acPolicyLegacyLegacy          =2          # from enum AcPlotPolicyForLegacyDwgs
	acPolicyLegacyQuery           =1          # from enum AcPlotPolicyForLegacyDwgs

class AcPlotPolicyForNewDwgs(IntEnum):
	acPolicyNewDefault            =0          # from enum AcPlotPolicyForNewDwgs
	acPolicyNewLegacy             =1          # from enum AcPlotPolicyForNewDwgs

class AcPlotRotation(IntEnum):
	ac0degrees                    =0          # from enum AcPlotRotation
	ac180degrees                  =2          # from enum AcPlotRotation
	ac270degrees                  =3          # from enum AcPlotRotation
	ac90degrees                   =1          # from enum AcPlotRotation

class AcPlotScale(IntEnum):
	ac100_1                       =32         # from enum AcPlotScale
	ac10_1                        =31         # from enum AcPlotScale
	ac1_1                         =16         # from enum AcPlotScale
	ac1_10                        =21         # from enum AcPlotScale
	ac1_100                       =27         # from enum AcPlotScale
	ac1_128in_1ft                 =1          # from enum AcPlotScale
	ac1_16                        =22         # from enum AcPlotScale
	ac1_16in_1ft                  =4          # from enum AcPlotScale
	ac1_2                         =17         # from enum AcPlotScale
	ac1_20                        =23         # from enum AcPlotScale
	ac1_2in_1ft                   =10         # from enum AcPlotScale
	ac1_30                        =24         # from enum AcPlotScale
	ac1_32in_1ft                  =3          # from enum AcPlotScale
	ac1_4                         =18         # from enum AcPlotScale
	ac1_40                        =25         # from enum AcPlotScale
	ac1_4in_1ft                   =8          # from enum AcPlotScale
	ac1_5                         =19         # from enum AcPlotScale
	ac1_50                        =26         # from enum AcPlotScale
	ac1_64in_1ft                  =2          # from enum AcPlotScale
	ac1_8                         =20         # from enum AcPlotScale
	ac1_8in_1ft                   =6          # from enum AcPlotScale
	ac1ft_1ft                     =15         # from enum AcPlotScale
	ac1in_1ft                     =12         # from enum AcPlotScale
	ac2_1                         =28         # from enum AcPlotScale
	ac3_16in_1ft                  =7          # from enum AcPlotScale
	ac3_32in_1ft                  =5          # from enum AcPlotScale
	ac3_4in_1ft                   =11         # from enum AcPlotScale
	ac3_8in_1ft                   =9          # from enum AcPlotScale
	ac3in_1ft                     =13         # from enum AcPlotScale
	ac4_1                         =29         # from enum AcPlotScale
	ac6in_1ft                     =14         # from enum AcPlotScale
	ac8_1                         =30         # from enum AcPlotScale
	acScaleToFit                  =0          # from enum AcPlotScale

class AcPlotType(IntEnum):
	acDisplay                     =0          # from enum AcPlotType
	acExtents                     =1          # from enum AcPlotType
	acLayout                      =5          # from enum AcPlotType
	acLimits                      =2          # from enum AcPlotType
	acView                        =3          # from enum AcPlotType
	acWindow                      =4          # from enum AcPlotType

class AcPointCloudColorType(IntEnum):
	acByColor                     =1          # from enum AcPointCloudColorType
	acTrueColor                   =0          # from enum AcPointCloudColorType

class AcPointCloudExStylizationType(IntEnum):
	acClassification              =5          # from enum AcPointCloudExStylizationType
	acElevation                   =4          # from enum AcPointCloudExStylizationType
	acIntensities                 =3          # from enum AcPointCloudExStylizationType
	acNormals                     =2          # from enum AcPointCloudExStylizationType
	acObject                      =1          # from enum AcPointCloudExStylizationType
	acRGB                         =0          # from enum AcPointCloudExStylizationType

class AcPointCloudIntensityStyle(IntEnum):
	acIntensityBlue               =4          # from enum AcPointCloudIntensityStyle
	acIntensityEditableFlag       =5          # from enum AcPointCloudIntensityStyle
	acIntensityGrayscale          =0          # from enum AcPointCloudIntensityStyle
	acIntensityGreen              =3          # from enum AcPointCloudIntensityStyle
	acIntensityRainbow            =1          # from enum AcPointCloudIntensityStyle
	acIntensityRed                =2          # from enum AcPointCloudIntensityStyle

class AcPointCloudStylizationType(IntEnum):
	acIntensity                   =3          # from enum AcPointCloudStylizationType
	acNormal                      =2          # from enum AcPointCloudStylizationType
	acObjectColor                 =1          # from enum AcPointCloudStylizationType
	acScanColor                   =0          # from enum AcPointCloudStylizationType

class AcPolylineType(IntEnum):
	acCubicSplinePoly             =3          # from enum AcPolylineType
	acFitCurvePoly                =1          # from enum AcPolylineType
	acQuadSplinePoly              =2          # from enum AcPolylineType
	acSimplePoly                  =0          # from enum AcPolylineType

class AcPolymeshType(IntEnum):
	acBezierSurfaceMesh           =8          # from enum AcPolymeshType
	acCubicSurfaceMesh            =6          # from enum AcPolymeshType
	acQuadSurfaceMesh             =5          # from enum AcPolymeshType
	acSimpleMesh                  =0          # from enum AcPolymeshType

class AcPredefBlockType(IntEnum):
	acBlockBox                    =3          # from enum AcPredefBlockType
	acBlockCircle                 =2          # from enum AcPredefBlockType
	acBlockHexagon                =4          # from enum AcPredefBlockType
	acBlockImperial               =0          # from enum AcPredefBlockType
	acBlockSlot                   =1          # from enum AcPredefBlockType
	acBlockTriangle               =5          # from enum AcPredefBlockType
	acBlockUserDefined            =6          # from enum AcPredefBlockType

class AcPreviewMode(IntEnum):
	acFullPreview                 =1          # from enum AcPreviewMode
	acPartialPreview              =0          # from enum AcPreviewMode

class AcPrinterSpoolAlert(IntEnum):
	acPrinterAlertOnce            =1          # from enum AcPrinterSpoolAlert
	acPrinterAlwaysAlert          =0          # from enum AcPrinterSpoolAlert
	acPrinterNeverAlert           =3          # from enum AcPrinterSpoolAlert
	acPrinterNeverAlertLogOnce    =2          # from enum AcPrinterSpoolAlert

class AcProxyImage(IntEnum):
	acProxyBoundingBox            =2          # from enum AcProxyImage
	acProxyNotShow                =0          # from enum AcProxyImage
	acProxyShow                   =1          # from enum AcProxyImage

class AcRegenType(IntEnum):
	acActiveViewport              =0          # from enum AcRegenType
	acAllViewports                =1          # from enum AcRegenType

class AcRotationAngle(IntEnum):
	acDegrees000                  =0          # from enum AcRotationAngle
	acDegrees090                  =1          # from enum AcRotationAngle
	acDegrees180                  =2          # from enum AcRotationAngle
	acDegrees270                  =3          # from enum AcRotationAngle
	acDegreesUnknown              =-1         # from enum AcRotationAngle

class AcRowType(IntEnum):
	acDataRow                     =1          # from enum AcRowType
	acHeaderRow                   =4          # from enum AcRowType
	acTitleRow                    =2          # from enum AcRowType
	acUnknownRow                  =0          # from enum AcRowType

class AcSaveAsType(IntEnum):
	ac2000_Template               =14         # from enum AcSaveAsType
	ac2000_dwg                    =12         # from enum AcSaveAsType
	ac2000_dxf                    =13         # from enum AcSaveAsType
	ac2004_Template               =26         # from enum AcSaveAsType
	ac2004_dwg                    =24         # from enum AcSaveAsType
	ac2004_dxf                    =25         # from enum AcSaveAsType
	ac2007_Template               =38         # from enum AcSaveAsType
	ac2007_dwg                    =36         # from enum AcSaveAsType
	ac2007_dxf                    =37         # from enum AcSaveAsType
	ac2010_Template               =50         # from enum AcSaveAsType
	ac2010_dwg                    =48         # from enum AcSaveAsType
	ac2010_dxf                    =49         # from enum AcSaveAsType
	ac2013_Template               =62         # from enum AcSaveAsType
	ac2013_dwg                    =60         # from enum AcSaveAsType
	ac2013_dxf                    =61         # from enum AcSaveAsType
	ac2018_Template               =66         # from enum AcSaveAsType
	ac2018_dwg                    =64         # from enum AcSaveAsType
	ac2018_dxf                    =65         # from enum AcSaveAsType
	acNative                      =64         # from enum AcSaveAsType
	acR12_dxf                     =1          # from enum AcSaveAsType
	acR13_dwg                     =4          # from enum AcSaveAsType
	acR13_dxf                     =5          # from enum AcSaveAsType
	acR14_dwg                     =8          # from enum AcSaveAsType
	acR14_dxf                     =9          # from enum AcSaveAsType
	acR15_Template                =14         # from enum AcSaveAsType
	acR15_dwg                     =12         # from enum AcSaveAsType
	acR15_dxf                     =13         # from enum AcSaveAsType
	acR18_Template                =26         # from enum AcSaveAsType
	acR18_dwg                     =24         # from enum AcSaveAsType
	acR18_dxf                     =25         # from enum AcSaveAsType
	acUnknown                     =-1         # from enum AcSaveAsType

class AcSectionGeneration(IntEnum):
	acSectionGenerationDestinationFile=64         # from enum AcSectionGeneration
	acSectionGenerationDestinationNewBlock=16         # from enum AcSectionGeneration
	acSectionGenerationDestinationReplaceBlock=32         # from enum AcSectionGeneration
	acSectionGenerationSourceAllObjects=1          # from enum AcSectionGeneration
	acSectionGenerationSourceSelectedObjects=2          # from enum AcSectionGeneration

class AcSectionState(IntEnum):
	acSectionStateBoundary        =2          # from enum AcSectionState
	acSectionStatePlane           =1          # from enum AcSectionState
	acSectionStateVolume          =4          # from enum AcSectionState

class AcSectionState2(IntEnum):
	acSectionState2Boundary       =4          # from enum AcSectionState2
	acSectionState2Plane          =1          # from enum AcSectionState2
	acSectionState2Slice          =2          # from enum AcSectionState2
	acSectionState2Volume         =8          # from enum AcSectionState2

class AcSectionSubItem(IntEnum):
	acSectionSubItemBackLine      =8          # from enum AcSectionSubItem
	acSectionSubItemBackLineBottom=32         # from enum AcSectionSubItem
	acSectionSubItemBackLineTop   =16         # from enum AcSectionSubItem
	acSectionSubItemSectionLine   =1          # from enum AcSectionSubItem
	acSectionSubItemSectionLineBottom=4          # from enum AcSectionSubItem
	acSectionSubItemSectionLineTop=2          # from enum AcSectionSubItem
	acSectionSubItemVerticalLineBottom=128        # from enum AcSectionSubItem
	acSectionSubItemVerticalLineTop=64         # from enum AcSectionSubItem
	acSectionSubItemkNone         =0          # from enum AcSectionSubItem

class AcSectionType(IntEnum):
	acSectionType2dSection        =2          # from enum AcSectionType
	acSectionType3dSection        =4          # from enum AcSectionType
	acSectionTypeLiveSection      =1          # from enum AcSectionType

class AcSegmentAngleType(IntEnum):
	acDegrees15                   =1          # from enum AcSegmentAngleType
	acDegrees30                   =2          # from enum AcSegmentAngleType
	acDegrees45                   =3          # from enum AcSegmentAngleType
	acDegrees60                   =4          # from enum AcSegmentAngleType
	acDegrees90                   =6          # from enum AcSegmentAngleType
	acDegreesAny                  =0          # from enum AcSegmentAngleType
	acDegreesHorz                 =12         # from enum AcSegmentAngleType

class AcSelect(IntEnum):
	acSelectionSetAll             =5          # from enum AcSelect
	acSelectionSetCrossing        =1          # from enum AcSelect
	acSelectionSetCrossingPolygon =7          # from enum AcSelect
	acSelectionSetFence           =2          # from enum AcSelect
	acSelectionSetLast            =4          # from enum AcSelect
	acSelectionSetPrevious        =3          # from enum AcSelect
	acSelectionSetWindow          =0          # from enum AcSelect
	acSelectionSetWindowPolygon   =6          # from enum AcSelect

class AcSelectType(IntEnum):
	acTableSelectCrossing         =2          # from enum AcSelectType
	acTableSelectWindow           =1          # from enum AcSelectType

class AcShadePlot(IntEnum):
	acShadePlotAsDisplayed        =0          # from enum AcShadePlot
	acShadePlotHidden             =2          # from enum AcShadePlot
	acShadePlotRendered           =3          # from enum AcShadePlot
	acShadePlotWireframe          =1          # from enum AcShadePlot

class AcShadowDisplayType(IntEnum):
	acCastsAndReceivesShadows     =0          # from enum AcShadowDisplayType
	acCastsShadows                =1          # from enum AcShadowDisplayType
	acIgnoreShadows               =3          # from enum AcShadowDisplayType
	acReceivesShadows             =2          # from enum AcShadowDisplayType

class AcSplineFrameType(IntEnum):
	acHide                        =1          # from enum AcSplineFrameType
	acShow                        =0          # from enum AcSplineFrameType

class AcSplineKnotParameterizationType(IntEnum):
	acChord                       =0          # from enum AcSplineKnotParameterizationType
	acCustomParameterization      =15         # from enum AcSplineKnotParameterizationType
	acSqrtChord                   =1          # from enum AcSplineKnotParameterizationType
	acUniformParam                =2          # from enum AcSplineKnotParameterizationType

class AcSplineMethodType(IntEnum):
	acControlVertices             =1          # from enum AcSplineMethodType
	acFit                         =0          # from enum AcSplineMethodType

class AcTableDirection(IntEnum):
	acTableBottomToTop            =1          # from enum AcTableDirection
	acTableTopToBottom            =0          # from enum AcTableDirection

class AcTableFlowDirection(IntEnum):
	acTableFlowDownOrUp           =2          # from enum AcTableFlowDirection
	acTableFlowLeft               =4          # from enum AcTableFlowDirection
	acTableFlowRight              =1          # from enum AcTableFlowDirection

class AcTableStyleOverrides(IntEnum):
	acCellAlign                   =130        # from enum AcTableStyleOverrides
	acCellBackgroundColor         =132        # from enum AcTableStyleOverrides
	acCellBackgroundFillNone      =131        # from enum AcTableStyleOverrides
	acCellBottomGridColor         =138        # from enum AcTableStyleOverrides
	acCellBottomGridLineWeight    =142        # from enum AcTableStyleOverrides
	acCellBottomVisibility        =146        # from enum AcTableStyleOverrides
	acCellContentColor            =133        # from enum AcTableStyleOverrides
	acCellDataType                =148        # from enum AcTableStyleOverrides
	acCellLeftGridColor           =139        # from enum AcTableStyleOverrides
	acCellLeftGridLineWeight      =143        # from enum AcTableStyleOverrides
	acCellLeftVisibility          =147        # from enum AcTableStyleOverrides
	acCellRightGridColor          =137        # from enum AcTableStyleOverrides
	acCellRightGridLineWeight     =141        # from enum AcTableStyleOverrides
	acCellRightVisibility         =145        # from enum AcTableStyleOverrides
	acCellTextHeight              =135        # from enum AcTableStyleOverrides
	acCellTextStyle               =134        # from enum AcTableStyleOverrides
	acCellTopGridColor            =136        # from enum AcTableStyleOverrides
	acCellTopGridLineWeight       =140        # from enum AcTableStyleOverrides
	acCellTopVisibility           =144        # from enum AcTableStyleOverrides
	acDataHorzBottomColor         =54         # from enum AcTableStyleOverrides
	acDataHorzBottomLineWeight    =84         # from enum AcTableStyleOverrides
	acDataHorzBottomVisibility    =114        # from enum AcTableStyleOverrides
	acDataHorzInsideColor         =53         # from enum AcTableStyleOverrides
	acDataHorzInsideLineWeight    =83         # from enum AcTableStyleOverrides
	acDataHorzInsideVisibility    =113        # from enum AcTableStyleOverrides
	acDataHorzTopColor            =52         # from enum AcTableStyleOverrides
	acDataHorzTopLineWeight       =82         # from enum AcTableStyleOverrides
	acDataHorzTopVisibility       =112        # from enum AcTableStyleOverrides
	acDataRowAlignment            =17         # from enum AcTableStyleOverrides
	acDataRowColor                =8          # from enum AcTableStyleOverrides
	acDataRowDataType             =26         # from enum AcTableStyleOverrides
	acDataRowFillColor            =14         # from enum AcTableStyleOverrides
	acDataRowFillNone             =11         # from enum AcTableStyleOverrides
	acDataRowTextHeight           =23         # from enum AcTableStyleOverrides
	acDataRowTextStyle            =20         # from enum AcTableStyleOverrides
	acDataVertInsideColor         =56         # from enum AcTableStyleOverrides
	acDataVertInsideLineWeight    =86         # from enum AcTableStyleOverrides
	acDataVertInsideVisibility    =116        # from enum AcTableStyleOverrides
	acDataVertLeftColor           =55         # from enum AcTableStyleOverrides
	acDataVertLeftLineWeight      =85         # from enum AcTableStyleOverrides
	acDataVertLeftVisibility      =115        # from enum AcTableStyleOverrides
	acDataVertRightColor          =57         # from enum AcTableStyleOverrides
	acDataVertRightLineWeight     =87         # from enum AcTableStyleOverrides
	acDataVertRightVisibility     =117        # from enum AcTableStyleOverrides
	acFlowDirection               =3          # from enum AcTableStyleOverrides
	acHeaderHorzBottomColor       =48         # from enum AcTableStyleOverrides
	acHeaderHorzBottomLineWeight  =78         # from enum AcTableStyleOverrides
	acHeaderHorzBottomVisibility  =108        # from enum AcTableStyleOverrides
	acHeaderHorzInsideColor       =47         # from enum AcTableStyleOverrides
	acHeaderHorzInsideLineWeight  =77         # from enum AcTableStyleOverrides
	acHeaderHorzInsideVisibility  =107        # from enum AcTableStyleOverrides
	acHeaderHorzTopColor          =46         # from enum AcTableStyleOverrides
	acHeaderHorzTopLineWeight     =76         # from enum AcTableStyleOverrides
	acHeaderHorzTopVisibility     =106        # from enum AcTableStyleOverrides
	acHeaderRowAlignment          =16         # from enum AcTableStyleOverrides
	acHeaderRowColor              =7          # from enum AcTableStyleOverrides
	acHeaderRowDataType           =25         # from enum AcTableStyleOverrides
	acHeaderRowFillColor          =13         # from enum AcTableStyleOverrides
	acHeaderRowFillNone           =10         # from enum AcTableStyleOverrides
	acHeaderRowTextHeight         =22         # from enum AcTableStyleOverrides
	acHeaderRowTextStyle          =19         # from enum AcTableStyleOverrides
	acHeaderSuppressed            =2          # from enum AcTableStyleOverrides
	acHeaderVertInsideColor       =50         # from enum AcTableStyleOverrides
	acHeaderVertInsideLineWeight  =80         # from enum AcTableStyleOverrides
	acHeaderVertInsideVisibility  =110        # from enum AcTableStyleOverrides
	acHeaderVertLeftColor         =49         # from enum AcTableStyleOverrides
	acHeaderVertLeftLineWeight    =79         # from enum AcTableStyleOverrides
	acHeaderVertLeftVisibility    =109        # from enum AcTableStyleOverrides
	acHeaderVertRightColor        =51         # from enum AcTableStyleOverrides
	acHeaderVertRightLineWeight   =81         # from enum AcTableStyleOverrides
	acHeaderVertRightVisibility   =111        # from enum AcTableStyleOverrides
	acHorzCellMargin              =4          # from enum AcTableStyleOverrides
	acTitleHorzBottomColor        =42         # from enum AcTableStyleOverrides
	acTitleHorzBottomLineWeight   =72         # from enum AcTableStyleOverrides
	acTitleHorzBottomVisibility   =102        # from enum AcTableStyleOverrides
	acTitleHorzInsideColor        =41         # from enum AcTableStyleOverrides
	acTitleHorzInsideLineWeight   =71         # from enum AcTableStyleOverrides
	acTitleHorzInsideVisibility   =101        # from enum AcTableStyleOverrides
	acTitleHorzTopColor           =40         # from enum AcTableStyleOverrides
	acTitleHorzTopLineWeight      =70         # from enum AcTableStyleOverrides
	acTitleHorzTopVisibility      =100        # from enum AcTableStyleOverrides
	acTitleRowAlignment           =15         # from enum AcTableStyleOverrides
	acTitleRowColor               =6          # from enum AcTableStyleOverrides
	acTitleRowDataType            =24         # from enum AcTableStyleOverrides
	acTitleRowFillColor           =12         # from enum AcTableStyleOverrides
	acTitleRowFillNone            =9          # from enum AcTableStyleOverrides
	acTitleRowTextHeight          =21         # from enum AcTableStyleOverrides
	acTitleRowTextStyle           =18         # from enum AcTableStyleOverrides
	acTitleSuppressed             =1          # from enum AcTableStyleOverrides
	acTitleVertInsideColor        =44         # from enum AcTableStyleOverrides
	acTitleVertInsideLineWeight   =74         # from enum AcTableStyleOverrides
	acTitleVertInsideVisibility   =104        # from enum AcTableStyleOverrides
	acTitleVertLeftColor          =43         # from enum AcTableStyleOverrides
	acTitleVertLeftLineWeight     =73         # from enum AcTableStyleOverrides
	acTitleVertLeftVisibility     =103        # from enum AcTableStyleOverrides
	acTitleVertRightColor         =45         # from enum AcTableStyleOverrides
	acTitleVertRightLineWeight    =75         # from enum AcTableStyleOverrides
	acTitleVertRightVisibility    =105        # from enum AcTableStyleOverrides
	acVertCellMargin              =5          # from enum AcTableStyleOverrides

class AcTextAlignmentType(IntEnum):
	acCenterAlignment             =1          # from enum AcTextAlignmentType
	acLeftAlignment               =0          # from enum AcTextAlignmentType
	acRightAlignment              =2          # from enum AcTextAlignmentType

class AcTextAngleType(IntEnum):
	acAlwaysRightReadingAngle     =2          # from enum AcTextAngleType
	acHorizontalAngle             =1          # from enum AcTextAngleType
	acInsertAngle                 =0          # from enum AcTextAngleType

class AcTextAttachmentDirection(IntEnum):
	acAttachmentHorizontal        =0          # from enum AcTextAttachmentDirection
	acAttachmentVertical          =1          # from enum AcTextAttachmentDirection

class AcTextAttachmentType(IntEnum):
	acAttachmentAllLine           =8          # from enum AcTextAttachmentType
	acAttachmentBottomLine        =7          # from enum AcTextAttachmentType
	acAttachmentBottomOfBottom    =6          # from enum AcTextAttachmentType
	acAttachmentBottomOfTop       =2          # from enum AcTextAttachmentType
	acAttachmentBottomOfTopLine   =3          # from enum AcTextAttachmentType
	acAttachmentMiddle            =4          # from enum AcTextAttachmentType
	acAttachmentMiddleOfBottom    =5          # from enum AcTextAttachmentType
	acAttachmentMiddleOfTop       =1          # from enum AcTextAttachmentType
	acAttachmentTopOfTop          =0          # from enum AcTextAttachmentType

class AcTextFontStyle(IntEnum):
	acFontBold                    =2          # from enum AcTextFontStyle
	acFontBoldItalic              =3          # from enum AcTextFontStyle
	acFontItalic                  =1          # from enum AcTextFontStyle
	acFontRegular                 =0          # from enum AcTextFontStyle

class AcTextGenerationFlag(IntEnum):
	acTextNoFlag            =0
	acTextFlagBackward            =2          # from enum AcTextGenerationFlag
	acTextFlagUpsideDown          =4          # from enum AcTextGenerationFlag

class AcToolbarDockStatus(IntEnum):
	acToolbarDockBottom           =1          # from enum AcToolbarDockStatus
	acToolbarDockLeft             =2          # from enum AcToolbarDockStatus
	acToolbarDockRight            =3          # from enum AcToolbarDockStatus
	acToolbarDockTop              =0          # from enum AcToolbarDockStatus
	acToolbarFloating             =4          # from enum AcToolbarDockStatus

class AcToolbarItemType(IntEnum):
	acToolbarButton               =0          # from enum AcToolbarItemType
	acToolbarControl              =2          # from enum AcToolbarItemType
	acToolbarFlyout               =3          # from enum AcToolbarItemType
	acToolbarSeparator            =1          # from enum AcToolbarItemType

class AcUnderlayLayerOverrideType(IntEnum):
	acApplied                     =1          # from enum AcUnderlayLayerOverrideType
	acNoOverrides                 =0          # from enum AcUnderlayLayerOverrideType

class AcUnits(IntEnum):
	acArchitectural               =4          # from enum AcUnits
	acDecimal                     =2          # from enum AcUnits
	acDefaultUnits                =-1         # from enum AcUnits
	acEngineering                 =3          # from enum AcUnits
	acFractional                  =5          # from enum AcUnits
	acScientific                  =1          # from enum AcUnits

class AcValueDataType(IntEnum):
	acBuffer                      =128        # from enum AcValueDataType
	acDate                        =8          # from enum AcValueDataType
	acDouble                      =2          # from enum AcValueDataType
	acGeneral                     =512        # from enum AcValueDataType
	acLong                        =1          # from enum AcValueDataType
	acObjectId                    =64         # from enum AcValueDataType
	acPoint2d                     =16         # from enum AcValueDataType
	acPoint3d                     =32         # from enum AcValueDataType
	acResbuf                      =256        # from enum AcValueDataType
	acString                      =4          # from enum AcValueDataType
	acUnknownDataType             =0          # from enum AcValueDataType

class AcValueUnitType(IntEnum):
	acUnitAngle                   =2          # from enum AcValueUnitType
	acUnitArea                    =4          # from enum AcValueUnitType
	acUnitDistance                =1          # from enum AcValueUnitType
	acUnitVolume                  =8          # from enum AcValueUnitType
	acUnitless                    =0          # from enum AcValueUnitType

class AcVerticalAlignment(IntEnum):
	acVerticalAlignmentBaseline   =0          # from enum AcVerticalAlignment
	acVerticalAlignmentBottom     =1          # from enum AcVerticalAlignment
	acVerticalAlignmentMiddle     =2          # from enum AcVerticalAlignment
	acVerticalAlignmentTop        =3          # from enum AcVerticalAlignment

class AcVerticalTextAttachmentType(IntEnum):
	acAttachmentCenter            =0          # from enum AcVerticalTextAttachmentType
	acAttachmentLinedCenter       =1          # from enum AcVerticalTextAttachmentType

class AcViewportScale(IntEnum):
	acVp100_1                     =18         # from enum AcViewportScale
	acVp10_1                      =17         # from enum AcViewportScale
	acVp1_1                       =2          # from enum AcViewportScale
	acVp1_10                      =7          # from enum AcViewportScale
	acVp1_100                     =13         # from enum AcViewportScale
	acVp1_128in_1ft               =19         # from enum AcViewportScale
	acVp1_16                      =8          # from enum AcViewportScale
	acVp1_16in_1ft                =22         # from enum AcViewportScale
	acVp1_2                       =3          # from enum AcViewportScale
	acVp1_20                      =9          # from enum AcViewportScale
	acVp1_2in_1ft                 =28         # from enum AcViewportScale
	acVp1_30                      =10         # from enum AcViewportScale
	acVp1_32in_1ft                =21         # from enum AcViewportScale
	acVp1_4                       =4          # from enum AcViewportScale
	acVp1_40                      =11         # from enum AcViewportScale
	acVp1_4in_1ft                 =26         # from enum AcViewportScale
	acVp1_5                       =5          # from enum AcViewportScale
	acVp1_50                      =12         # from enum AcViewportScale
	acVp1_64in_1ft                =20         # from enum AcViewportScale
	acVp1_8                       =6          # from enum AcViewportScale
	acVp1_8in_1ft                 =24         # from enum AcViewportScale
	acVp1and1_2in_1ft             =31         # from enum AcViewportScale
	acVp1ft_1ft                   =34         # from enum AcViewportScale
	acVp1in_1ft                   =30         # from enum AcViewportScale
	acVp2_1                       =14         # from enum AcViewportScale
	acVp3_16in_1ft                =25         # from enum AcViewportScale
	acVp3_32in_1ft                =23         # from enum AcViewportScale
	acVp3_4in_1ft                 =29         # from enum AcViewportScale
	acVp3_8in_1ft                 =27         # from enum AcViewportScale
	acVp3in_1ft                   =32         # from enum AcViewportScale
	acVp4_1                       =15         # from enum AcViewportScale
	acVp6in_1ft                   =33         # from enum AcViewportScale
	acVp8_1                       =16         # from enum AcViewportScale
	acVpCustomScale               =1          # from enum AcViewportScale
	acVpScaleToFit                =0          # from enum AcViewportScale

class AcViewportSplitType(IntEnum):
	acViewport2Horizontal         =0          # from enum AcViewportSplitType
	acViewport2Vertical           =1          # from enum AcViewportSplitType
	acViewport3Above              =6          # from enum AcViewportSplitType
	acViewport3Below              =7          # from enum AcViewportSplitType
	acViewport3Horizontal         =4          # from enum AcViewportSplitType
	acViewport3Left               =2          # from enum AcViewportSplitType
	acViewport3Right              =3          # from enum AcViewportSplitType
	acViewport3Vertical           =5          # from enum AcViewportSplitType
	acViewport4                   =8          # from enum AcViewportSplitType

class AcWindowState(IntEnum):
	acMax                         =3          # from enum AcWindowState
	acMin                         =2          # from enum AcWindowState
	acNorm                        =1          # from enum AcWindowState

class AcWireframeType(IntEnum):
	acIsolines                    =0          # from enum AcWireframeType
	acIsoparms                    =1          # from enum AcWireframeType

class AcXRefDemandLoad(IntEnum):
	acDemandLoadDisabled          =0          # from enum AcXRefDemandLoad
	acDemandLoadEnabled           =1          # from enum AcXRefDemandLoad
	acDemandLoadEnabledWithCopy   =2          # from enum AcXRefDemandLoad

class AcZoomScaleType(IntEnum):
	acZoomScaledAbsolute          =0          # from enum AcZoomScaleType
	acZoomScaledRelative          =1          # from enum AcZoomScaleType
	acZoomScaledRelativePSpace    =2          # from enum AcZoomScaleType

class AcadSecurityParamsConstants(IntEnum):
	ACADSECURITYPARAMS_ALGID_RC4  =26625      # from enum AcadSecurityParamsConstants

class AcadSecurityParamsType(IntEnum):
	ACADSECURITYPARAMS_ADD_TIMESTAMP=32         # from enum AcadSecurityParamsType
	ACADSECURITYPARAMS_ENCRYPT_DATA=1          # from enum AcadSecurityParamsType
	ACADSECURITYPARAMS_ENCRYPT_PROPS=2          # from enum AcadSecurityParamsType
	ACADSECURITYPARAMS_SIGN_DATA  =16         # from enum AcadSecurityParamsType

class AdeskDxfCode(IntEnum):
	kDxfInvalid        = -9999
	kDxfXDictionary     = -6
	kDxfPReactors       = -5
	kDxfOperator        = -4
	kDxfXDataStart      = -3
	kDxfHeaderId        = -2
	kDxfFirstEntId      = -2
	kDxfEnd             = -1
	kDxfStart           = 0
	kDxfText            = 1
	kDxfXRefPath        = 1
	kDxfShapeName       = 2
	kDxfBlockName       = 2
	kDxfAttributeTag    = 2
	kDxfSymbolTableName = 2
	kDxfMstyleName      = 2
	kDxfSymTableRecName = 2
	kDxfAttributePrompt = 3
	kDxfDimStyleName    = 3
	kDxfLinetypeProse   = 3
	kDxfTextFontFile    = 3
	kDxfDescription     = 3
	kDxfDimPostStr      = 3
	kDxfTextBigFontFile = 4
	kDxfDimAPostStr     = 4
	kDxfCLShapeName     = 4
	kDxfSymTableRecComments = 4
	kDxfHandle          = 5
	kDxfDimBlk          = 5
	kDxfDimBlk1         = 6
	kDxfLinetypeName    = 6
	kDxfDimBlk2         = 7
	kDxfTextStyleName   = 7
	kDxfLayerName       = 8
	kDxfCLShapeText     = 9

	kDxfXCoord         = 10

	kDxfYCoord         = 20

	kDxfZCoord         = 30

	kDxfElevation      = 38
	kDxfThickness      = 39

	kDxfReal           = 40
	kDxfViewportHeight = 40
	kDxfTxtSize        = 40
	kDxfTxtStyleXScale = 41
	kDxfViewWidth      = 41
	kDxfViewportAspect = 41
	kDxfTxtStylePSize  = 42
	kDxfViewLensLength = 42
	kDxfViewFrontClip  = 43
	kDxfViewBackClip   = 44
	kDxfShapeXOffset   = 44
	kDxfShapeYOffset   = 45
	kDxfViewHeight     = 45
	kDxfShapeScale     = 46
	kDxfPixelScale     = 47

	kDxfLinetypeScale  = 48

	kDxfDashLength     = 49
	kDxfMlineOffset    = 49
	kDxfLinetypeElement = 49

	kDxfAngle          = 50
	kDxfViewportSnapAngle = 50 # deprecated
	kDxfViewportTwist  = 51

	kDxfVisibility          = 60
	kDxfViewportGridDisplay = 60
	kDxfLayerLinetype       = 61
	kDxfViewportGridMajor   = 61
	kDxfColor               = 62
	# Removed codes intended
	# only for internal
	# use:  63-65
	kDxfHasSubentities = 66
	kDxfViewportVisibility = 67
	kDxfViewportActive = 68
	kDxfViewportNumber = 69

	kDxfInt16          = 70
	kDxfViewMode       = 71
	kDxfCircleSides    = 72
	kDxfViewportZoom   = 73
	kDxfViewportIcon   = 74
	kDxfViewportSnap   = 75
	kDxfViewportGrid   = 76
	kDxfViewportSnapStyle= 77
	kDxfViewportSnapPair= 78

	kDxfRegAppFlags    = 71

	kDxfTxtStyleFlags  = 71
	kDxfLinetypeAlign  = 72
	kDxfLinetypePDC    = 73

	kDxfInt32          = 90
	kDxfVertexIdentifier = 91
	# Subclass Section Marker
	#
	# to be followed by subclass name.
	#
	kDxfSubclass            = 100
	kDxfEmbeddedObjectStart = 101
	kDxfControlString       = 102

	# DimVarTableRecords have been using 5 for a
	# string value.  With R13, they get a handle
	# value as well.  Since 5 is already in use,
	# we use 105 for this special case.
	#
	kDxfDimVarHandle = 105

	kDxfUCSOrg         = 110
	kDxfUCSOriX        = 111
	kDxfUCSOriY        = 112

	kDxfXReal          = 140
	kDxfViewBrightness = 141
	kDxfViewContrast   = 142

	# 64-bit integers can only be used with
	# AcDbDwgVersion kDHL_1024 and higher.
	#
	kDxfInt64          = 160

	kDxfXInt16         = 170
	# 180 - 189 cannot be used

	# 190-199 are invalid

	kDxfNormalX        = 210
	kDxfNormalY        = 220
	kDxfNormalZ        = 230

	# 260-269 are invalid

	kDxfXXInt16        = 270

	kDxfInt8                = 280
	kDxfRenderMode          = 281
	kDxfDefaultLightingType = 282
	kDxfShadowFlags         = 284

	kDxfBool                = 290
	kDxfDefaultLightingOn   = 292

	#  More string values 300-309
	kDxfXTextString   = 300

	#  Arbitrary Binary Chunks 310-319
	kDxfBinaryChunk   = 310

	#  Arbitrary Object Handles 320-329
	kDxfArbHandle     = 320

	kDxfSoftPointerId    = 330 # 330-339
	kDxfViewBackgroundId = 332 # softPointer to background of viewport and viewporttable record
	kDxfShadePlotId      = 333 # softPointer to shade plot visual style or render preset
	kDxfLiveSectionId      = 334 # softPointer to LiveSection of view, viewport and viewporttable record
	kDxfLiveSectionName    = 309 # LiveSection Name

	kDxfHardPointerId    = 340 # 340-349
	kDxfObjVisualStyleId = 345
	kDxfVpVisualStyleId = 346
	kDxfMaterialId       = 347 # hardpointer reference to AcDbMaterial
	kDxfVisualStyleId    = 348 # hardpointer reference to visual style
	kDxfDragVisualStyleId = 349 # hardpointer reference to visual style

	kDxfSoftOwnershipId  = 350 # 350-359

	kDxfHardOwnershipId  = 360 # 360-369
	kDxfSunId            = 361 # hardownership reference to sun object

	# New base entity properties
	# Lineweight is either an integer
	# or "BYLAYER" or "BYBLOCK"
	kDxfLineWeight        = 370
	kDxfPlotStyleNameType = 380
	kDxfPlotStyleNameId   = 390
	kDxfXXXInt16          = 400

	kDxfLayoutName     = 410

	# Extended color information for base entities

	kDxfColorRGB       = 420
	kDxfColorName      = 430

	# New base entity property Alpha is an integer
	kDxfAlpha          = 440

	kDxfGradientObjType  = 450
	kDxfGradientPatType  = 451
	kDxfGradientTintType = 452
	kDxfGradientColCount = 453
	kDxfGradientAngle    = 460
	kDxfGradientShift    = 461
	kDxfGradientTintVal  = 462
	kDxfGradientColVal   = 463
	kDxfGradientName     = 470

	kDxfFaceStyleId = 480
	kDxfEdgeStyleId = 481

	kDxfComment        = 999

	kDxfXdAsciiString  = 1000
	kDxfRegAppName     = 1001
	kDxfXdControlString = 1002
	kDxfXdLayerName    = 1003
	kDxfXdBinaryChunk  = 1004
	kDxfXdHandle       = 1005

	kDxfXdXCoord       = 1010
	kDxfXdYCoord       = 1020
	kDxfXdZCoord       = 1030

	kDxfXdWorldXCoord  = 1011
	kDxfXdWorldYCoord  = 1021
	kDxfXdWorldZCoord  = 1031

	kDxfXdWorldXDisp   = 1012
	kDxfXdWorldYDisp   = 1022
	kDxfXdWorldZDisp   = 1032

	kDxfXdWorldXDir    = 1013
	kDxfXdWorldYDir    = 1023
	kDxfXdWorldZDir    = 1033

	kDxfXdReal         = 1040
	kDxfXdDist         = 1041
	kDxfXdScale        = 1042

	kDxfXdInteger16    = 1070
	kDxfXdInteger32    = 1071
	# This enum value should always be set to whatever the highest
	# enum value is.
	kDxfXdMax          =  kDxfXdInteger32


class AcEntityTransparency(StrEnum):
	_ignore_ = ('v','attr_name')
	ByLayer   = 'ByLayer'
	ByBlock   = 'ByBlock'
	# --- Динамическая генерация значений
	for v in range(0, 91):
		# Создаем имя атрибута от t_0 до t_90
		attr_name = f"t_{v}"
		locals()[attr_name] = str(v)


class uArrowSymbol(StrEnum):
	empty			="" 
	_ClosedBlank	="_ClosedBlank" 
	_Closed			="_Closed" 
	_Dot			="_Dot" 
	_ArchTick		="_ArchTick" 
	_Oblique		="_Oblique" 
	_Open			="_Open" 
	_Origin			="_Origin" 
	_Origin2		="_Origin2" 
	_Open30			="_Open30" 
	_Open90			="_Open90" 
	_DotSmall		="_DotSmall" 
	_DotBlank		="_DotBlank" 
	_Small			="_Small" 
	_BoxBlank		="_BoxBlank" 
	_BoxFilled		="_BoxFilled" 
	_DatumBlank		="_DatumBlank" 
	_DatumFilled	="_DatumFilled" 
	_Integral		="_Integral" 
	_None			="_None" 
	_User			="_User" 