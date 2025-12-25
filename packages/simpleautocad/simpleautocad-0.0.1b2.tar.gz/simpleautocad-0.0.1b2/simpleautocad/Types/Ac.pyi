from enum import Enum as Enum, IntEnum, StrEnum

class Ac3DPolylineType(IntEnum):
    acCubicSpline3DPoly = 2
    acQuadSpline3DPoly = 1
    acSimple3DPoly = 0

class AcARXDemandLoad(IntEnum):
    acDemanLoadDisable = 0
    acDemandLoadCmdInvoke = 2
    acDemandLoadOnObjectDetect = 1

class AcActiveSpace(IntEnum):
    acModelSpace = 1
    acPaperSpace = 0

class AcAlignment(IntEnum):
    acAlignmentAligned = 3
    acAlignmentBottomCenter = 13
    acAlignmentBottomLeft = 12
    acAlignmentBottomRight = 14
    acAlignmentCenter = 1
    acAlignmentFit = 5
    acAlignmentLeft = 0
    acAlignmentMiddle = 4
    acAlignmentMiddleCenter = 10
    acAlignmentMiddleLeft = 9
    acAlignmentMiddleRight = 11
    acAlignmentRight = 2
    acAlignmentTopCenter = 7
    acAlignmentTopLeft = 6
    acAlignmentTopRight = 8

class AcAlignmentPointAcquisition(IntEnum):
    acAlignPntAcquisitionAutomatic = 0
    acAlignPntAcquisitionShiftToAcquire = 1

class AcAngleUnits(IntEnum):
    acDegreeMinuteSeconds = 1
    acDegrees = 0
    acGrads = 2
    acRadians = 3

class AcAttachmentPoint(IntEnum):
    acAttachmentPointBottomCenter = 8
    acAttachmentPointBottomLeft = 7
    acAttachmentPointBottomRight = 9
    acAttachmentPointMiddleCenter = 5
    acAttachmentPointMiddleLeft = 4
    acAttachmentPointMiddleRight = 6
    acAttachmentPointTopCenter = 2
    acAttachmentPointTopLeft = 1
    acAttachmentPointTopRight = 3

class AcAttributeMode(IntEnum):
    acAttributeModeConstant = 2
    acAttributeModeInvisible = 1
    acAttributeModeLockPosition = 16
    acAttributeModeMultipleLine = 32
    acAttributeModeNormal = 0
    acAttributeModePreset = 8
    acAttributeModeVerify = 4

class AcBlockConnectionType(IntEnum):
    acConnectBase = 1
    acConnectExtents = 0

class AcBlockScaling(IntEnum):
    acAny = 0
    acUniform = 1

class AcBoolean(IntEnum):
    acFalse = 0
    acTrue = 1

class AcBooleanType(IntEnum):
    acIntersection = 1
    acSubtraction = 2
    acUnion = 0

class AcCellAlignment(IntEnum):
    acBottomCenter = 8
    acBottomLeft = 7
    acBottomRight = 9
    acMiddleCenter = 5
    acMiddleLeft = 4
    acMiddleRight = 6
    acTopCenter = 2
    acTopLeft = 1
    acTopRight = 3

class AcCellContentLayout(IntEnum):
    acCellContentLayoutFlow = 1
    acCellContentLayoutStackedHorizontal = 2
    acCellContentLayoutStackedVertical = 4

class AcCellContentType(IntEnum):
    acCellContentTypeBlock = 4
    acCellContentTypeField = 2
    acCellContentTypeUnknown = 0
    acCellContentTypeValue = 1

class AcCellEdgeMask(IntEnum):
    acBottomMask = 4
    acLeftMask = 8
    acRightMask = 2
    acTopMask = 1

class AcCellMargin(IntEnum):
    acCellMarginBottom = 4
    acCellMarginHorzSpacing = 16
    acCellMarginLeft = 2
    acCellMarginRight = 8
    acCellMarginTop = 1
    acCellMarginVertSpacing = 32

class AcCellOption(IntEnum):
    kCellOptionNone = 0
    kInheritCellFormat = 1

class AcCellProperty(IntEnum):
    acAlignmentProperty = 32
    acAllCellProperties = 524287
    acAutoScale = 32768
    acBackgroundColor = 128
    acBitProperties = 245760
    acContentColor = 64
    acContentLayout = 262144
    acContentProperties = 33662
    acDataFormat = 4
    acDataType = 2
    acDataTypeAndFormat = 6
    acEnableBackgroundColor = 16384
    acFlowDirBtoT = 131072
    acInvalidCellProperty = 0
    acLock = 1
    acMarginBottom = 8192
    acMarginLeft = 1024
    acMarginRight = 4096
    acMarginTop = 2048
    acMergeAll = 65536
    acRotation = 8
    acScale = 16
    acTextHeight = 512
    acTextStyle = 256

class AcCellState(IntEnum):
    acCellStateContentLocked = 1
    acCellStateContentModified = 32
    acCellStateContentReadOnly = 2
    acCellStateFormatLocked = 4
    acCellStateFormatModified = 64
    acCellStateFormatReadOnly = 8
    acCellStateLinked = 16
    acCellStateNone = 0

class AcCellType(IntEnum):
    acBlockCell = 2
    acTextCell = 1
    acUnknownCell = 0

class AcColor(IntEnum):
    acByBlock = 0
    acByLayer = 256
    acRed = 1
    acYellow = 2
    acGreen = 3
    acCyan = 4
    acBlue = 5
    acMagenta = 6
    acWhite = 7
    attr_name = ...

class AcColorMethod(IntEnum):
    acColorMethodByACI = 195
    acColorMethodByBlock = 193
    acColorMethodByLayer = 192
    acColorMethodByRGB = 194
    acColorMethodForeground = 197

class AcCoordinateSystem(IntEnum):
    acDisplayDCS = 2
    acOCS = 4
    acPaperSpaceDCS = 3
    acUCS = 1
    acWorld = 0

class AcDataLinkUpdateDirection(IntEnum):
    acUpdateDataFromSource = 1
    acUpdateSourceFromData = 2

class AcDataLinkUpdateOption(IntEnum):
    acUpdateOptionIncludeXrefs = 1048576
    acUpdateOptionNone = 0
    acUpdateOptionOverwriteContentModifiedAfterUpdate = 131072
    acUpdateOptionOverwriteFormatModifiedAfterUpdate = 262144
    acUpdateOptionUpdateFullSourceRange = 524288

class AcDimArcLengthSymbol(IntEnum):
    acSymAbove = 1
    acSymInFront = 0
    acSymNone = 2

class AcDimArrowheadType(IntEnum):
    acArrowArchTick = 4
    acArrowBoxBlank = 14
    acArrowBoxFilled = 15
    acArrowClosed = 2
    acArrowClosedBlank = 1
    acArrowDatumBlank = 16
    acArrowDatumFilled = 17
    acArrowDefault = 0
    acArrowDot = 3
    acArrowDotBlank = 12
    acArrowDotSmall = 11
    acArrowIntegral = 18
    acArrowNone = 19
    acArrowOblique = 5
    acArrowOpen = 6
    acArrowOpen30 = 10
    acArrowOpen90 = 9
    acArrowOrigin = 7
    acArrowOrigin2 = 8
    acArrowSmall = 13
    acArrowUserDefined = 20

class AcDimCenterType(IntEnum):
    acCenterLine = 1
    acCenterMark = 0
    acCenterNone = 2

class AcDimFit(IntEnum):
    acArrowsOnly = 1
    acBestFit = 3
    acTextAndArrows = 0
    acTextOnly = 2

class AcDimFractionType(IntEnum):
    acDiagonal = 1
    acHorizontal = 0
    acNotStacked = 2

class AcDimHorizontalJustification(IntEnum):
    acFirstExtensionLine = 1
    acHorzCentered = 0
    acOverFirstExtension = 3
    acOverSecondExtension = 4
    acSecondExtensionLine = 2

class AcDimLUnits(IntEnum):
    acDimLArchitectural = 4
    acDimLDecimal = 2
    acDimLEngineering = 3
    acDimLFractional = 5
    acDimLScientific = 1
    acDimLWindowsDesktop = 6

class AcDimPrecision(IntEnum):
    acDimPrecisionEight = 8
    acDimPrecisionFive = 5
    acDimPrecisionFour = 4
    acDimPrecisionOne = 1
    acDimPrecisionSeven = 7
    acDimPrecisionSix = 6
    acDimPrecisionThree = 3
    acDimPrecisionTwo = 2
    acDimPrecisionZero = 0

class AcDimTextMovement(IntEnum):
    acDimLineWithText = 0
    acMoveTextAddLeader = 1
    acMoveTextNoLeader = 2

class AcDimToleranceJustify(IntEnum):
    acTolBottom = 0
    acTolMiddle = 1
    acTolTop = 2

class AcDimToleranceMethod(IntEnum):
    acTolBasic = 4
    acTolDeviation = 2
    acTolLimits = 3
    acTolNone = 0
    acTolSymmetrical = 1

class AcDimUnits(IntEnum):
    acDimArchitectural = 6
    acDimArchitecturalStacked = 4
    acDimDecimal = 2
    acDimEngineering = 3
    acDimFractional = 7
    acDimFractionalStacked = 5
    acDimScientific = 1
    acDimWindowsDesktop = 8

class AcDimVerticalJustification(IntEnum):
    acAbove = 1
    acJIS = 3
    acOutside = 2
    acUnder = 4
    acVertCentered = 0

class AcDragDisplayMode(IntEnum):
    acDragDisplayAutomatically = 2
    acDragDisplayOnRequest = 1
    acDragDoNotDisplay = 0

class AcDrawLeaderOrderType(IntEnum):
    acDrawLeaderHeadFirst = 0
    acDrawLeaderTailFirst = 1

class AcDrawMLeaderOrderType(IntEnum):
    acDrawContentFirst = 0
    acDrawLeaderFirst = 1

class AcDrawingAreaSCMCommand(IntEnum):
    acEnableSCM = 2
    acEnableSCMOptions = 1
    acEnter = 0

class AcDrawingAreaSCMDefault(IntEnum):
    acRepeatLastCommand = 0
    acSCM = 1

class AcDrawingAreaSCMEdit(IntEnum):
    acEdRepeatLastCommand = 0
    acEdSCM = 1

class AcDrawingAreaShortCutMenu(IntEnum):
    acNoDrawingAreaShortCutMenu = 0
    acUseDefaultDrawingAreaShortCutMenu = 1

class AcDrawingDirection(IntEnum):
    acBottomToTop = 4
    acByStyle = 5
    acLeftToRight = 1
    acRightToLeft = 2
    acTopToBottom = 3

class AcDynamicBlockReferencePropertyUnitsType(IntEnum):
    acAngular = 1
    acArea = 3
    acDistance = 2
    acNoUnits = 0

class AcEntityName(IntEnum):
    ac3dFace = 1
    ac3dPolyline = 2
    ac3dSolid = 3
    acArc = 4
    acAttribute = 5
    acAttributeReference = 6
    acBlockReference = 7
    acCircle = 8
    acDgnUnderlay = 47
    acDim3PointAngular = 41
    acDimAligned = 9
    acDimAngular = 10
    acDimArcLength = 44
    acDimDiametric = 12
    acDimOrdinate = 13
    acDimRadial = 14
    acDimRadialLarge = 45
    acDimRotated = 15
    acDwfUnderlay = 46
    acEllipse = 16
    acExternalReference = 42
    acGroup = 37
    acHatch = 17
    acLeader = 18
    acLine = 19
    acMInsertBlock = 38
    acMLeader = 48
    acMLine = 40
    acMtext = 21
    acNurbSurface = 51
    acPViewport = 35
    acPdfUnderlay = 50
    acPoint = 22
    acPolyfaceMesh = 39
    acPolyline = 23
    acPolylineLight = 24
    acPolymesh = 25
    acRaster = 26
    acRay = 27
    acRegion = 28
    acShape = 29
    acSolid = 30
    acSpline = 31
    acSubDMesh = 49
    acTable = 43
    acText = 32
    acTolerance = 33
    acTrace = 34
    acXline = 36

class AcExtendOption(IntEnum):
    acExtendBoth = 3
    acExtendNone = 0
    acExtendOtherEntity = 2
    acExtendThisEntity = 1

class AcFormatOption(IntEnum):
    acForEditing = 1
    acForExpression = 2
    acIgnoreMtextFormat = 8
    acUseMaximumPrecision = 4
    kFormatOptionNone = 0

class AcGradientPatternType(IntEnum):
    acPreDefinedGradient = 0
    acUserDefinedGradient = 1

class AcGridLineStyle(IntEnum):
    acGridLineStyleDouble = 2
    acGridLineStyleSingle = 1

class AcGridLineType(IntEnum):
    acHorzBottom = 4
    acHorzInside = 2
    acHorzTop = 1
    acInvalidGridLine = 0
    acVertInside = 16
    acVertLeft = 8
    acVertRight = 32

class AcHatchObjectType(IntEnum):
    acGradientObject = 1
    acHatchObject = 0

class AcHatchStyle(IntEnum):
    acHatchStyleIgnore = 2
    acHatchStyleNormal = 0
    acHatchStyleOuter = 1

class AcHelixConstrainType(IntEnum):
    acHeight = 2
    acTurnHeight = 0
    acTurns = 1

class AcHelixTwistType(IntEnum):
    acCCW = 0
    acCW = 1

class AcHorizontalAlignment(IntEnum):
    acHorizontalAlignmentAligned = 3
    acHorizontalAlignmentCenter = 1
    acHorizontalAlignmentFit = 5
    acHorizontalAlignmentLeft = 0
    acHorizontalAlignmentMiddle = 4
    acHorizontalAlignmentRight = 2

class AcISOPenWidth(IntEnum):
    acPenWidth013 = 13
    acPenWidth018 = 18
    acPenWidth025 = 25
    acPenWidth035 = 35
    acPenWidth050 = 50
    acPenWidth070 = 70
    acPenWidth100 = 100
    acPenWidth140 = 140
    acPenWidth200 = 200
    acPenWidthUnk = -1

class AcInsertUnits(IntEnum):
    acInsertUnitsAngstroms = 11
    acInsertUnitsAstronomicalUnits = 18
    acInsertUnitsCentimeters = 5
    acInsertUnitsDecameters = 15
    acInsertUnitsDecimeters = 14
    acInsertUnitsFeet = 2
    acInsertUnitsGigameters = 17
    acInsertUnitsHectometers = 16
    acInsertUnitsInches = 1
    acInsertUnitsKilometers = 7
    acInsertUnitsLightYears = 19
    acInsertUnitsMeters = 6
    acInsertUnitsMicroinches = 8
    acInsertUnitsMicrons = 13
    acInsertUnitsMiles = 3
    acInsertUnitsMillimeters = 4
    acInsertUnitsMils = 9
    acInsertUnitsNanometers = 12
    acInsertUnitsParsecs = 20
    acInsertUnitsUSSurveyFeet = 21
    acInsertUnitsUSSurveyInch = 22
    acInsertUnitsUSSurveyMile = 24
    acInsertUnitsUSSurveyYard = 23
    acInsertUnitsUnitless = 0
    acInsertUnitsYards = 10

class AcInsertUnitsAction(IntEnum):
    acInsertUnitsAutoAssign = 1
    acInsertUnitsPrompt = 0

class AcKeyboardAccelerator(IntEnum):
    acPreferenceClassic = 0
    acPreferenceCustom = 1

class AcKeyboardPriority(IntEnum):
    acKeyboardEntry = 1
    acKeyboardEntryExceptScripts = 2
    acKeyboardRunningObjSnap = 0

class AcLayerStateMask(IntEnum):
    acLsAll = 65535
    acLsColor = 32
    acLsFrozen = 2
    acLsLineType = 64
    acLsLineWeight = 128
    acLsLocked = 4
    acLsNewViewport = 16
    acLsNone = 0
    acLsOn = 1
    acLsPlot = 8
    acLsPlotStyle = 256

class AcLeaderType(IntEnum):
    acLineNoArrow = 0
    acLineWithArrow = 2
    acSplineNoArrow = 1
    acSplineWithArrow = 3

class AcLineSpacingStyle(IntEnum):
    acLineSpacingStyleAtLeast = 1
    acLineSpacingStyleExactly = 2

class AcLineWeight(IntEnum):
    acLnWt000 = 0
    acLnWt005 = 5
    acLnWt009 = 9
    acLnWt013 = 13
    acLnWt015 = 15
    acLnWt018 = 18
    acLnWt020 = 20
    acLnWt025 = 25
    acLnWt030 = 30
    acLnWt035 = 35
    acLnWt040 = 40
    acLnWt050 = 50
    acLnWt053 = 53
    acLnWt060 = 60
    acLnWt070 = 70
    acLnWt080 = 80
    acLnWt090 = 90
    acLnWt100 = 100
    acLnWt106 = 106
    acLnWt120 = 120
    acLnWt140 = 140
    acLnWt158 = 158
    acLnWt200 = 200
    acLnWt211 = 211
    acLnWtByBlock = -2
    acLnWtByLayer = -1
    acLnWtByLwDefault = -3

class AcLoadPalette(IntEnum):
    acPaletteByDrawing = 0
    acPaletteBySession = 1

class AcLoftedSurfaceNormalType(IntEnum):
    acAllNormal = 5
    acEndsNormal = 4
    acFirstNormal = 2
    acLastNormal = 3
    acRuled = 0
    acSmooth = 1
    acUseDraftAngles = 6

class AcLoopType(IntEnum):
    acHatchLoopTypeDefault = 0
    acHatchLoopTypeDerived = 4
    acHatchLoopTypeExternal = 1
    acHatchLoopTypePolyline = 2
    acHatchLoopTypeTextbox = 8

class AcMLeaderContentType(IntEnum):
    acBlockContent = 1
    acMTextContent = 2
    acNoneContent = 0

class AcMLeaderType(IntEnum):
    acInVisibleLeader = 0
    acSplineLeader = 2
    acStraightLeader = 1

class AcMLineJustification(IntEnum):
    acBottom = 2
    acTop = 0
    acZero = 1

class AcMeasurementUnits(IntEnum):
    acEnglish = 0
    acMetric = 1

class AcMenuFileType(IntEnum):
    acMenuFileCompiled = 0
    acMenuFileSource = 1

class AcMenuGroupType(IntEnum):
    acBaseMenuGroup = 0
    acPartialMenuGroup = 1

class AcMenuItemType(IntEnum):
    acMenuItem = 0
    acMenuSeparator = 1
    acMenuSubMenu = 2

class AcMergeCellStyleOption(IntEnum):
    acMergeCellStyleConvertDuplicatesToOverrides = 4
    acMergeCellStyleCopyDuplicates = 1
    acMergeCellStyleIgnoreNewStyles = 8
    acMergeCellStyleNone = 0
    acMergeCellStyleOverwriteDuplicates = 2

class AcMeshCreaseType(IntEnum):
    acAlwaysCrease = 1
    acCreaseByLevel = 2
    acNoneCrease = 0

class AcOlePlotQuality(IntEnum):
    acOPQHighGraphics = 2
    acOPQLowGraphics = 1
    acOPQMonochrome = 0

class AcOleQuality(IntEnum):
    acOQGraphics = 2
    acOQHighPhoto = 4
    acOQLineArt = 0
    acOQPhoto = 3
    acOQText = 1

class AcOleType(IntEnum):
    acOTEmbedded = 2
    acOTLink = 1
    acOTStatic = 3

class AcOnOff(IntEnum):
    acOff = 0
    acOn = 1

class AcParseOption(IntEnum):
    acParseOptionNone = 0
    acPreserveMtextFormat = 2
    acSetDefaultFormat = 1

class AcPatternType(IntEnum):
    acHatchPatternTypeCustomDefined = 2
    acHatchPatternTypePreDefined = 1
    acHatchPatternTypeUserDefined = 0

class AcPlotOrientation(IntEnum):
    acPlotOrientationLandscape = 1
    acPlotOrientationPortrait = 0

class AcPlotPaperUnits(IntEnum):
    acInches = 0
    acMillimeters = 1
    acPixels = 2

class AcPlotPolicy(IntEnum):
    acPolicyLegacy = 1
    acPolicyNamed = 0

class AcPlotPolicyForLegacyDwgs(IntEnum):
    acPolicyLegacyDefault = 0
    acPolicyLegacyLegacy = 2
    acPolicyLegacyQuery = 1

class AcPlotPolicyForNewDwgs(IntEnum):
    acPolicyNewDefault = 0
    acPolicyNewLegacy = 1

class AcPlotRotation(IntEnum):
    ac0degrees = 0
    ac180degrees = 2
    ac270degrees = 3
    ac90degrees = 1

class AcPlotScale(IntEnum):
    ac100_1 = 32
    ac10_1 = 31
    ac1_1 = 16
    ac1_10 = 21
    ac1_100 = 27
    ac1_128in_1ft = 1
    ac1_16 = 22
    ac1_16in_1ft = 4
    ac1_2 = 17
    ac1_20 = 23
    ac1_2in_1ft = 10
    ac1_30 = 24
    ac1_32in_1ft = 3
    ac1_4 = 18
    ac1_40 = 25
    ac1_4in_1ft = 8
    ac1_5 = 19
    ac1_50 = 26
    ac1_64in_1ft = 2
    ac1_8 = 20
    ac1_8in_1ft = 6
    ac1ft_1ft = 15
    ac1in_1ft = 12
    ac2_1 = 28
    ac3_16in_1ft = 7
    ac3_32in_1ft = 5
    ac3_4in_1ft = 11
    ac3_8in_1ft = 9
    ac3in_1ft = 13
    ac4_1 = 29
    ac6in_1ft = 14
    ac8_1 = 30
    acScaleToFit = 0

class AcPlotType(IntEnum):
    acDisplay = 0
    acExtents = 1
    acLayout = 5
    acLimits = 2
    acView = 3
    acWindow = 4

class AcPointCloudColorType(IntEnum):
    acByColor = 1
    acTrueColor = 0

class AcPointCloudExStylizationType(IntEnum):
    acClassification = 5
    acElevation = 4
    acIntensities = 3
    acNormals = 2
    acObject = 1
    acRGB = 0

class AcPointCloudIntensityStyle(IntEnum):
    acIntensityBlue = 4
    acIntensityEditableFlag = 5
    acIntensityGrayscale = 0
    acIntensityGreen = 3
    acIntensityRainbow = 1
    acIntensityRed = 2

class AcPointCloudStylizationType(IntEnum):
    acIntensity = 3
    acNormal = 2
    acObjectColor = 1
    acScanColor = 0

class AcPolylineType(IntEnum):
    acCubicSplinePoly = 3
    acFitCurvePoly = 1
    acQuadSplinePoly = 2
    acSimplePoly = 0

class AcPolymeshType(IntEnum):
    acBezierSurfaceMesh = 8
    acCubicSurfaceMesh = 6
    acQuadSurfaceMesh = 5
    acSimpleMesh = 0

class AcPredefBlockType(IntEnum):
    acBlockBox = 3
    acBlockCircle = 2
    acBlockHexagon = 4
    acBlockImperial = 0
    acBlockSlot = 1
    acBlockTriangle = 5
    acBlockUserDefined = 6

class AcPreviewMode(IntEnum):
    acFullPreview = 1
    acPartialPreview = 0

class AcPrinterSpoolAlert(IntEnum):
    acPrinterAlertOnce = 1
    acPrinterAlwaysAlert = 0
    acPrinterNeverAlert = 3
    acPrinterNeverAlertLogOnce = 2

class AcProxyImage(IntEnum):
    acProxyBoundingBox = 2
    acProxyNotShow = 0
    acProxyShow = 1

class AcRegenType(IntEnum):
    acActiveViewport = 0
    acAllViewports = 1

class AcRotationAngle(IntEnum):
    acDegrees000 = 0
    acDegrees090 = 1
    acDegrees180 = 2
    acDegrees270 = 3
    acDegreesUnknown = -1

class AcRowType(IntEnum):
    acDataRow = 1
    acHeaderRow = 4
    acTitleRow = 2
    acUnknownRow = 0

class AcSaveAsType(IntEnum):
    ac2000_Template = 14
    ac2000_dwg = 12
    ac2000_dxf = 13
    ac2004_Template = 26
    ac2004_dwg = 24
    ac2004_dxf = 25
    ac2007_Template = 38
    ac2007_dwg = 36
    ac2007_dxf = 37
    ac2010_Template = 50
    ac2010_dwg = 48
    ac2010_dxf = 49
    ac2013_Template = 62
    ac2013_dwg = 60
    ac2013_dxf = 61
    ac2018_Template = 66
    ac2018_dwg = 64
    ac2018_dxf = 65
    acNative = 64
    acR12_dxf = 1
    acR13_dwg = 4
    acR13_dxf = 5
    acR14_dwg = 8
    acR14_dxf = 9
    acR15_Template = 14
    acR15_dwg = 12
    acR15_dxf = 13
    acR18_Template = 26
    acR18_dwg = 24
    acR18_dxf = 25
    acUnknown = -1

class AcSectionGeneration(IntEnum):
    acSectionGenerationDestinationFile = 64
    acSectionGenerationDestinationNewBlock = 16
    acSectionGenerationDestinationReplaceBlock = 32
    acSectionGenerationSourceAllObjects = 1
    acSectionGenerationSourceSelectedObjects = 2

class AcSectionState(IntEnum):
    acSectionStateBoundary = 2
    acSectionStatePlane = 1
    acSectionStateVolume = 4

class AcSectionState2(IntEnum):
    acSectionState2Boundary = 4
    acSectionState2Plane = 1
    acSectionState2Slice = 2
    acSectionState2Volume = 8

class AcSectionSubItem(IntEnum):
    acSectionSubItemBackLine = 8
    acSectionSubItemBackLineBottom = 32
    acSectionSubItemBackLineTop = 16
    acSectionSubItemSectionLine = 1
    acSectionSubItemSectionLineBottom = 4
    acSectionSubItemSectionLineTop = 2
    acSectionSubItemVerticalLineBottom = 128
    acSectionSubItemVerticalLineTop = 64
    acSectionSubItemkNone = 0

class AcSectionType(IntEnum):
    acSectionType2dSection = 2
    acSectionType3dSection = 4
    acSectionTypeLiveSection = 1

class AcSegmentAngleType(IntEnum):
    acDegrees15 = 1
    acDegrees30 = 2
    acDegrees45 = 3
    acDegrees60 = 4
    acDegrees90 = 6
    acDegreesAny = 0
    acDegreesHorz = 12

class AcSelect(IntEnum):
    acSelectionSetAll = 5
    acSelectionSetCrossing = 1
    acSelectionSetCrossingPolygon = 7
    acSelectionSetFence = 2
    acSelectionSetLast = 4
    acSelectionSetPrevious = 3
    acSelectionSetWindow = 0
    acSelectionSetWindowPolygon = 6

class AcSelectType(IntEnum):
    acTableSelectCrossing = 2
    acTableSelectWindow = 1

class AcShadePlot(IntEnum):
    acShadePlotAsDisplayed = 0
    acShadePlotHidden = 2
    acShadePlotRendered = 3
    acShadePlotWireframe = 1

class AcShadowDisplayType(IntEnum):
    acCastsAndReceivesShadows = 0
    acCastsShadows = 1
    acIgnoreShadows = 3
    acReceivesShadows = 2

class AcSplineFrameType(IntEnum):
    acHide = 1
    acShow = 0

class AcSplineKnotParameterizationType(IntEnum):
    acChord = 0
    acCustomParameterization = 15
    acSqrtChord = 1
    acUniformParam = 2

class AcSplineMethodType(IntEnum):
    acControlVertices = 1
    acFit = 0

class AcTableDirection(IntEnum):
    acTableBottomToTop = 1
    acTableTopToBottom = 0

class AcTableFlowDirection(IntEnum):
    acTableFlowDownOrUp = 2
    acTableFlowLeft = 4
    acTableFlowRight = 1

class AcTableStyleOverrides(IntEnum):
    acCellAlign = 130
    acCellBackgroundColor = 132
    acCellBackgroundFillNone = 131
    acCellBottomGridColor = 138
    acCellBottomGridLineWeight = 142
    acCellBottomVisibility = 146
    acCellContentColor = 133
    acCellDataType = 148
    acCellLeftGridColor = 139
    acCellLeftGridLineWeight = 143
    acCellLeftVisibility = 147
    acCellRightGridColor = 137
    acCellRightGridLineWeight = 141
    acCellRightVisibility = 145
    acCellTextHeight = 135
    acCellTextStyle = 134
    acCellTopGridColor = 136
    acCellTopGridLineWeight = 140
    acCellTopVisibility = 144
    acDataHorzBottomColor = 54
    acDataHorzBottomLineWeight = 84
    acDataHorzBottomVisibility = 114
    acDataHorzInsideColor = 53
    acDataHorzInsideLineWeight = 83
    acDataHorzInsideVisibility = 113
    acDataHorzTopColor = 52
    acDataHorzTopLineWeight = 82
    acDataHorzTopVisibility = 112
    acDataRowAlignment = 17
    acDataRowColor = 8
    acDataRowDataType = 26
    acDataRowFillColor = 14
    acDataRowFillNone = 11
    acDataRowTextHeight = 23
    acDataRowTextStyle = 20
    acDataVertInsideColor = 56
    acDataVertInsideLineWeight = 86
    acDataVertInsideVisibility = 116
    acDataVertLeftColor = 55
    acDataVertLeftLineWeight = 85
    acDataVertLeftVisibility = 115
    acDataVertRightColor = 57
    acDataVertRightLineWeight = 87
    acDataVertRightVisibility = 117
    acFlowDirection = 3
    acHeaderHorzBottomColor = 48
    acHeaderHorzBottomLineWeight = 78
    acHeaderHorzBottomVisibility = 108
    acHeaderHorzInsideColor = 47
    acHeaderHorzInsideLineWeight = 77
    acHeaderHorzInsideVisibility = 107
    acHeaderHorzTopColor = 46
    acHeaderHorzTopLineWeight = 76
    acHeaderHorzTopVisibility = 106
    acHeaderRowAlignment = 16
    acHeaderRowColor = 7
    acHeaderRowDataType = 25
    acHeaderRowFillColor = 13
    acHeaderRowFillNone = 10
    acHeaderRowTextHeight = 22
    acHeaderRowTextStyle = 19
    acHeaderSuppressed = 2
    acHeaderVertInsideColor = 50
    acHeaderVertInsideLineWeight = 80
    acHeaderVertInsideVisibility = 110
    acHeaderVertLeftColor = 49
    acHeaderVertLeftLineWeight = 79
    acHeaderVertLeftVisibility = 109
    acHeaderVertRightColor = 51
    acHeaderVertRightLineWeight = 81
    acHeaderVertRightVisibility = 111
    acHorzCellMargin = 4
    acTitleHorzBottomColor = 42
    acTitleHorzBottomLineWeight = 72
    acTitleHorzBottomVisibility = 102
    acTitleHorzInsideColor = 41
    acTitleHorzInsideLineWeight = 71
    acTitleHorzInsideVisibility = 101
    acTitleHorzTopColor = 40
    acTitleHorzTopLineWeight = 70
    acTitleHorzTopVisibility = 100
    acTitleRowAlignment = 15
    acTitleRowColor = 6
    acTitleRowDataType = 24
    acTitleRowFillColor = 12
    acTitleRowFillNone = 9
    acTitleRowTextHeight = 21
    acTitleRowTextStyle = 18
    acTitleSuppressed = 1
    acTitleVertInsideColor = 44
    acTitleVertInsideLineWeight = 74
    acTitleVertInsideVisibility = 104
    acTitleVertLeftColor = 43
    acTitleVertLeftLineWeight = 73
    acTitleVertLeftVisibility = 103
    acTitleVertRightColor = 45
    acTitleVertRightLineWeight = 75
    acTitleVertRightVisibility = 105
    acVertCellMargin = 5

class AcTextAlignmentType(IntEnum):
    acCenterAlignment = 1
    acLeftAlignment = 0
    acRightAlignment = 2

class AcTextAngleType(IntEnum):
    acAlwaysRightReadingAngle = 2
    acHorizontalAngle = 1
    acInsertAngle = 0

class AcTextAttachmentDirection(IntEnum):
    acAttachmentHorizontal = 0
    acAttachmentVertical = 1

class AcTextAttachmentType(IntEnum):
    acAttachmentAllLine = 8
    acAttachmentBottomLine = 7
    acAttachmentBottomOfBottom = 6
    acAttachmentBottomOfTop = 2
    acAttachmentBottomOfTopLine = 3
    acAttachmentMiddle = 4
    acAttachmentMiddleOfBottom = 5
    acAttachmentMiddleOfTop = 1
    acAttachmentTopOfTop = 0

class AcTextFontStyle(IntEnum):
    acFontBold = 2
    acFontBoldItalic = 3
    acFontItalic = 1
    acFontRegular = 0

class AcTextGenerationFlag(IntEnum):
    acTextNoFlag = 0
    acTextFlagBackward = 2
    acTextFlagUpsideDown = 4

class AcToolbarDockStatus(IntEnum):
    acToolbarDockBottom = 1
    acToolbarDockLeft = 2
    acToolbarDockRight = 3
    acToolbarDockTop = 0
    acToolbarFloating = 4

class AcToolbarItemType(IntEnum):
    acToolbarButton = 0
    acToolbarControl = 2
    acToolbarFlyout = 3
    acToolbarSeparator = 1

class AcUnderlayLayerOverrideType(IntEnum):
    acApplied = 1
    acNoOverrides = 0

class AcUnits(IntEnum):
    acArchitectural = 4
    acDecimal = 2
    acDefaultUnits = -1
    acEngineering = 3
    acFractional = 5
    acScientific = 1

class AcValueDataType(IntEnum):
    acBuffer = 128
    acDate = 8
    acDouble = 2
    acGeneral = 512
    acLong = 1
    acObjectId = 64
    acPoint2d = 16
    acPoint3d = 32
    acResbuf = 256
    acString = 4
    acUnknownDataType = 0

class AcValueUnitType(IntEnum):
    acUnitAngle = 2
    acUnitArea = 4
    acUnitDistance = 1
    acUnitVolume = 8
    acUnitless = 0

class AcVerticalAlignment(IntEnum):
    acVerticalAlignmentBaseline = 0
    acVerticalAlignmentBottom = 1
    acVerticalAlignmentMiddle = 2
    acVerticalAlignmentTop = 3

class AcVerticalTextAttachmentType(IntEnum):
    acAttachmentCenter = 0
    acAttachmentLinedCenter = 1

class AcViewportScale(IntEnum):
    acVp100_1 = 18
    acVp10_1 = 17
    acVp1_1 = 2
    acVp1_10 = 7
    acVp1_100 = 13
    acVp1_128in_1ft = 19
    acVp1_16 = 8
    acVp1_16in_1ft = 22
    acVp1_2 = 3
    acVp1_20 = 9
    acVp1_2in_1ft = 28
    acVp1_30 = 10
    acVp1_32in_1ft = 21
    acVp1_4 = 4
    acVp1_40 = 11
    acVp1_4in_1ft = 26
    acVp1_5 = 5
    acVp1_50 = 12
    acVp1_64in_1ft = 20
    acVp1_8 = 6
    acVp1_8in_1ft = 24
    acVp1and1_2in_1ft = 31
    acVp1ft_1ft = 34
    acVp1in_1ft = 30
    acVp2_1 = 14
    acVp3_16in_1ft = 25
    acVp3_32in_1ft = 23
    acVp3_4in_1ft = 29
    acVp3_8in_1ft = 27
    acVp3in_1ft = 32
    acVp4_1 = 15
    acVp6in_1ft = 33
    acVp8_1 = 16
    acVpCustomScale = 1
    acVpScaleToFit = 0

class AcViewportSplitType(IntEnum):
    acViewport2Horizontal = 0
    acViewport2Vertical = 1
    acViewport3Above = 6
    acViewport3Below = 7
    acViewport3Horizontal = 4
    acViewport3Left = 2
    acViewport3Right = 3
    acViewport3Vertical = 5
    acViewport4 = 8

class AcWindowState(IntEnum):
    acMax = 3
    acMin = 2
    acNorm = 1

class AcWireframeType(IntEnum):
    acIsolines = 0
    acIsoparms = 1

class AcXRefDemandLoad(IntEnum):
    acDemandLoadDisabled = 0
    acDemandLoadEnabled = 1
    acDemandLoadEnabledWithCopy = 2

class AcZoomScaleType(IntEnum):
    acZoomScaledAbsolute = 0
    acZoomScaledRelative = 1
    acZoomScaledRelativePSpace = 2

class AcadSecurityParamsConstants(IntEnum):
    ACADSECURITYPARAMS_ALGID_RC4 = 26625

class AcadSecurityParamsType(IntEnum):
    ACADSECURITYPARAMS_ADD_TIMESTAMP = 32
    ACADSECURITYPARAMS_ENCRYPT_DATA = 1
    ACADSECURITYPARAMS_ENCRYPT_PROPS = 2
    ACADSECURITYPARAMS_SIGN_DATA = 16

class AdeskDxfCode(IntEnum):
    kDxfInvalid = -9999
    kDxfXDictionary = -6
    kDxfPReactors = -5
    kDxfOperator = -4
    kDxfXDataStart = -3
    kDxfHeaderId = -2
    kDxfFirstEntId = -2
    kDxfEnd = -1
    kDxfStart = 0
    kDxfText = 1
    kDxfXRefPath = 1
    kDxfShapeName = 2
    kDxfBlockName = 2
    kDxfAttributeTag = 2
    kDxfSymbolTableName = 2
    kDxfMstyleName = 2
    kDxfSymTableRecName = 2
    kDxfAttributePrompt = 3
    kDxfDimStyleName = 3
    kDxfLinetypeProse = 3
    kDxfTextFontFile = 3
    kDxfDescription = 3
    kDxfDimPostStr = 3
    kDxfTextBigFontFile = 4
    kDxfDimAPostStr = 4
    kDxfCLShapeName = 4
    kDxfSymTableRecComments = 4
    kDxfHandle = 5
    kDxfDimBlk = 5
    kDxfDimBlk1 = 6
    kDxfLinetypeName = 6
    kDxfDimBlk2 = 7
    kDxfTextStyleName = 7
    kDxfLayerName = 8
    kDxfCLShapeText = 9
    kDxfXCoord = 10
    kDxfYCoord = 20
    kDxfZCoord = 30
    kDxfElevation = 38
    kDxfThickness = 39
    kDxfReal = 40
    kDxfViewportHeight = 40
    kDxfTxtSize = 40
    kDxfTxtStyleXScale = 41
    kDxfViewWidth = 41
    kDxfViewportAspect = 41
    kDxfTxtStylePSize = 42
    kDxfViewLensLength = 42
    kDxfViewFrontClip = 43
    kDxfViewBackClip = 44
    kDxfShapeXOffset = 44
    kDxfShapeYOffset = 45
    kDxfViewHeight = 45
    kDxfShapeScale = 46
    kDxfPixelScale = 47
    kDxfLinetypeScale = 48
    kDxfDashLength = 49
    kDxfMlineOffset = 49
    kDxfLinetypeElement = 49
    kDxfAngle = 50
    kDxfViewportSnapAngle = 50
    kDxfViewportTwist = 51
    kDxfVisibility = 60
    kDxfViewportGridDisplay = 60
    kDxfLayerLinetype = 61
    kDxfViewportGridMajor = 61
    kDxfColor = 62
    kDxfHasSubentities = 66
    kDxfViewportVisibility = 67
    kDxfViewportActive = 68
    kDxfViewportNumber = 69
    kDxfInt16 = 70
    kDxfViewMode = 71
    kDxfCircleSides = 72
    kDxfViewportZoom = 73
    kDxfViewportIcon = 74
    kDxfViewportSnap = 75
    kDxfViewportGrid = 76
    kDxfViewportSnapStyle = 77
    kDxfViewportSnapPair = 78
    kDxfRegAppFlags = 71
    kDxfTxtStyleFlags = 71
    kDxfLinetypeAlign = 72
    kDxfLinetypePDC = 73
    kDxfInt32 = 90
    kDxfVertexIdentifier = 91
    kDxfSubclass = 100
    kDxfEmbeddedObjectStart = 101
    kDxfControlString = 102
    kDxfDimVarHandle = 105
    kDxfUCSOrg = 110
    kDxfUCSOriX = 111
    kDxfUCSOriY = 112
    kDxfXReal = 140
    kDxfViewBrightness = 141
    kDxfViewContrast = 142
    kDxfInt64 = 160
    kDxfXInt16 = 170
    kDxfNormalX = 210
    kDxfNormalY = 220
    kDxfNormalZ = 230
    kDxfXXInt16 = 270
    kDxfInt8 = 280
    kDxfRenderMode = 281
    kDxfDefaultLightingType = 282
    kDxfShadowFlags = 284
    kDxfBool = 290
    kDxfDefaultLightingOn = 292
    kDxfXTextString = 300
    kDxfBinaryChunk = 310
    kDxfArbHandle = 320
    kDxfSoftPointerId = 330
    kDxfViewBackgroundId = 332
    kDxfShadePlotId = 333
    kDxfLiveSectionId = 334
    kDxfLiveSectionName = 309
    kDxfHardPointerId = 340
    kDxfObjVisualStyleId = 345
    kDxfVpVisualStyleId = 346
    kDxfMaterialId = 347
    kDxfVisualStyleId = 348
    kDxfDragVisualStyleId = 349
    kDxfSoftOwnershipId = 350
    kDxfHardOwnershipId = 360
    kDxfSunId = 361
    kDxfLineWeight = 370
    kDxfPlotStyleNameType = 380
    kDxfPlotStyleNameId = 390
    kDxfXXXInt16 = 400
    kDxfLayoutName = 410
    kDxfColorRGB = 420
    kDxfColorName = 430
    kDxfAlpha = 440
    kDxfGradientObjType = 450
    kDxfGradientPatType = 451
    kDxfGradientTintType = 452
    kDxfGradientColCount = 453
    kDxfGradientAngle = 460
    kDxfGradientShift = 461
    kDxfGradientTintVal = 462
    kDxfGradientColVal = 463
    kDxfGradientName = 470
    kDxfFaceStyleId = 480
    kDxfEdgeStyleId = 481
    kDxfComment = 999
    kDxfXdAsciiString = 1000
    kDxfRegAppName = 1001
    kDxfXdControlString = 1002
    kDxfXdLayerName = 1003
    kDxfXdBinaryChunk = 1004
    kDxfXdHandle = 1005
    kDxfXdXCoord = 1010
    kDxfXdYCoord = 1020
    kDxfXdZCoord = 1030
    kDxfXdWorldXCoord = 1011
    kDxfXdWorldYCoord = 1021
    kDxfXdWorldZCoord = 1031
    kDxfXdWorldXDisp = 1012
    kDxfXdWorldYDisp = 1022
    kDxfXdWorldZDisp = 1032
    kDxfXdWorldXDir = 1013
    kDxfXdWorldYDir = 1023
    kDxfXdWorldZDir = 1033
    kDxfXdReal = 1040
    kDxfXdDist = 1041
    kDxfXdScale = 1042
    kDxfXdInteger16 = 1070
    kDxfXdInteger32 = 1071
    kDxfXdMax = kDxfXdInteger32

class AcEntityTransparency(StrEnum):
    ByLayer = 'ByLayer'
    ByBlock = 'ByBlock'
    attr_name = ...

class uArrowSymbol(StrEnum):
    empty = ''
