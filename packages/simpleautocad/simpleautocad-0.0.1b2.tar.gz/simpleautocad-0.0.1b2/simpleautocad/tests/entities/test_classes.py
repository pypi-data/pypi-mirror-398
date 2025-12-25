from simpleautocad import *
import math
from colorama import init, Fore, Back, Style
init(autoreset=True) 

def prop_test(obj, name:str, assertion:type, access:AccessMode, write_value = None):
    print(f'Свойство: {Fore.CYAN}{name}{Fore.WHITE}, режим доступа: {Fore.CYAN}{access.name}{Fore.WHITE}')
    if access is AccessMode.ReadOnly:
        read_prop = getattr(obj, name)
        assert read_prop.__class__ is assertion
        print(f'\tчтение: {Fore.CYAN}{read_prop.__class__.__name__}{Fore.WHITE}({read_prop})')
    if access is AccessMode.ReadWrite:
        if write_value is not None:
            setattr(obj, name, write_value)
            print(f'\tзапись: {Fore.CYAN}{write_value.__class__.__name__}{Fore.WHITE}({write_value})')
        read_prop = getattr(obj, name)
        assert read_prop.__class__ is assertion
        print(f'\tчтение: {Fore.CYAN}{read_prop.__class__.__name__}{Fore.WHITE}({read_prop})')
        setattr(obj, name, read_prop)
        print(f'\tзапись: {Fore.CYAN}{read_prop.__class__.__name__}{Fore.WHITE}({read_prop})')
    if access is AccessMode.WriteOnly:
        setattr(obj, name, write_value)
        print(f'\tзапись: {Fore.CYAN}{write_value.__class__.__name__}{Fore.WHITE}({write_value})')
    if access is AccessMode.DenyFromAll:
        pass

def method_test(obj, name:str, ret_type = any, **kwargs):
    method = getattr(obj, name, None)
    result = None
    if callable(method):
        result = method(**kwargs)
        if ret_type is None or ret_type is any: pass
        else: assert ret_type is result.__class__
    else:
        raise AttributeError(f"Метод '{name}' не найден или не может быть вызван для объекта {type(obj).__name__}")
    items_str:str = ''
    for key, value in kwargs.items():
        items_str += f"{key} = {Fore.CYAN}{value.__class__.__name__}{Fore.WHITE}({value}); "
    if items_str: items_str = items_str[:-2]
    print(f'Метод: {Fore.CYAN}{name}{Fore.WHITE}({items_str})\n\tвернул: {Fore.CYAN}{result if result is None else result.__class__.__name__}{Fore.WHITE}({result})')
    return result

def test_AcadApplication(acad_app:AcadApplication):
    print(f"\nТестирование AcadApplication")
    print('-'*50)
    prop_test(acad_app, 'ActiveDocument', AcadDocument, AccessMode.ReadOnly)
    prop_test(acad_app, 'Application', AcadApplication, AccessMode.ReadOnly)
    prop_test(acad_app, 'Caption', str, AccessMode.ReadOnly)
    prop_test(acad_app, 'Documents', AcadDocuments, AccessMode.ReadOnly)
    prop_test(acad_app, 'FullName', str, AccessMode.ReadOnly)
    prop_test(acad_app, 'Height', float, AccessMode.ReadWrite)
    prop_test(acad_app, 'HWND', int, AccessMode.ReadOnly)
    prop_test(acad_app, 'LocaleId', int, AccessMode.ReadOnly)
    prop_test(acad_app, 'MenuBar', AcadMenuBar, AccessMode.ReadOnly)
    prop_test(acad_app, 'MenuGroups', AcadMenuGroups, AccessMode.ReadOnly)
    prop_test(acad_app, 'Name', str, AccessMode.ReadOnly)
    prop_test(acad_app, 'Path', str, AccessMode.ReadOnly)
    prop_test(acad_app, 'Preferences', AcadPreferences, AccessMode.ReadOnly)
    prop_test(acad_app, 'VBE', AppObject, AccessMode.ReadOnly)
    prop_test(acad_app, 'Version', str, AccessMode.ReadOnly)
    prop_test(acad_app, 'Visible', bool, AccessMode.ReadWrite)
    prop_test(acad_app, 'Width', float, AccessMode.ReadWrite)
    prop_test(acad_app, 'WindowLeft', int, AccessMode.ReadWrite)
    prop_test(acad_app, 'WindowState', int, AccessMode.ReadWrite)
    prop_test(acad_app, 'WindowTop', int, AccessMode.ReadWrite)

    
    for vp in acad_app.ActiveDocument.Viewports:
        method_test(acad_app,'StatusID',bool,VportObj=vp)

    method_test(acad_app,'Eval',None,Expression='n = 1 + 1')
    method_test(acad_app,'GetAcadState',AcadState)
    method_test(acad_app,'GetInterfaceObject',AppObject,ProgID=GetProgID(acad_app,'AcCmColor'))
    method_test(acad_app,'GetInterfaceObject',AppObject,ProgID=GetProgID(acad_app,'AcadLayerStateManager'))
    method_test(acad_app,'GetInterfaceObject',AppObject,ProgID=GetProgID(acad_app,'SecurityParams'))
    method_test(acad_app,'ListARX',vStringArray)
    method_test(acad_app,'Update',None)
    method_test(acad_app,'ZoomAll',None)
    method_test(acad_app,'ZoomCenter',None, Center=PyGePoint3d(),Magnify=10.5)
    method_test(acad_app,'ZoomExtents',None)
    # method_test(acad_app,'ZoomPickWindow',None)
    method_test(acad_app,'ZoomPrevious',None)
    method_test(acad_app,'ZoomScaled',None, Scale=0.5,ScaleType=AcZoomScaleType.acZoomScaledAbsolute)
    method_test(acad_app,'ZoomWindow',None, LowerLeft=PyGePoint3d(),UpperRight=PyGePoint3d(100,100))



def test_AcadDocument(acad_active_document:AcadDocument):
    print(f"\nТестирование AcadDocument")
    print('-'*50)
    doc = acad_active_document.Application.Documents.Add('New test doc')
    prop_test(doc, 'Active', bool, AccessMode.ReadOnly)
    prop_test(doc, 'ActiveDimStyle', AcadDimStyle, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveLayer', AcadLayer, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveLayout', AcadLayout, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveLinetype', AcadLineType, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveMaterial', AcadMaterial, AccessMode.ReadWrite)
    # prop_test(acad_active_document, 'ActivePViewport', AcadPViewport, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveSelectionSet', AcadSelectionSet, AccessMode.ReadOnly)
    prop_test(doc, 'ActiveSpace', AcActiveSpace, AccessMode.ReadWrite)
    prop_test(doc, 'ActiveTextStyle', AcadTextStyle, AccessMode.ReadWrite)
    ucs = doc.UserCoordinateSystems.Add(PyGePoint3d(10,10,10),PyGePoint3d(10,0,10),PyGePoint3d(0,10,10),'TestUCS')
    prop_test(doc, 'ActiveUCS', AcadUCS, AccessMode.ReadWrite,ucs)
    vp = doc.Viewports.Add('TestViewport')
    vp.Direction = PyGeVector3d(1,1,1)
    prop_test(doc, 'ActiveViewport', AcadViewport, AccessMode.ReadWrite, vp)
    prop_test(doc, 'Application', AcadApplication, AccessMode.ReadOnly)
    prop_test(doc, 'Database', IAcadDatabase, AccessMode.ReadOnly)
    prop_test(doc, 'FullName', str, AccessMode.ReadOnly)
    prop_test(doc, 'Height', float, AccessMode.ReadWrite)
    prop_test(doc, 'HWND', int, AccessMode.ReadOnly)
    # prop_test(acad_active_document, 'MSpace', bool, AccessMode.ReadWrite)
    prop_test(doc, 'Name', str, AccessMode.ReadOnly)
    prop_test(doc, 'ObjectSnapMode', bool, AccessMode.ReadWrite)
    prop_test(doc, 'Saved', bool, AccessMode.ReadOnly)
    prop_test(doc, 'SelectionSets', AcadSelectionSet, AccessMode.ReadOnly)
    prop_test(doc, 'SummaryInfo', AcadSummaryInfo, AccessMode.ReadOnly)
    prop_test(doc, 'Utility', AcadUtility, AccessMode.ReadOnly)
    prop_test(doc, 'Width', float, AccessMode.ReadWrite)
    prop_test(doc, 'WindowState', AcWindowState, AccessMode.ReadWrite)
    prop_test(doc, 'WindowTitle', str, AccessMode.ReadOnly)

    method_test(doc,'Activate', None)
    method_test(doc,'AuditInfo', None, FixError=False)
    method_test(doc,'Close', None)
    # method_test(acad_active_document,'GetVariable', any, Name='CPLOTSTYLE')
    # method_test(acad_active_document.Application.Documents,'Open', AcadDocument, Name='acad.dwt')

def test_transform(acad_app:AutoCAD, acad_active_document:AcadDocument, acad_model_space:AcadModelSpace):
    center = PyGePoint3d()
    size = 10
    acad_app.ZoomCenter(center,10.0)
    col_h = acad_app.uGetAcadAcCmColor()
    col_h.SetRGB(0,0,255)    
    col_m = acad_app.uGetAcadAcCmColor()
    col_m.SetRGB(0,255,0)
    col_s = acad_app.uGetAcadAcCmColor()
    col_s.SetRGB(255,0,0)
    ang_1_60 = -math.radians(360/60)

    pt1 = PyGePoint3d(center.x,center.y+size - size/10)
    pt2 = PyGePoint3d(center.x,center.y+size)
    line = acad_model_space.AddLine(pt1,pt2)
    hinspt = PyGePoint3d(pt1.x,pt1.y - size/6)
    hour = acad_model_space.AddMText(hinspt, size/6, '12')
    hour.Height = size/8
    hour.AttachmentPoint = AcAttachmentPoint.acAttachmentPointMiddleCenter
    hour.InsertionPoint = hinspt
    
    h_sec = acad_model_space.AddLine(PyGePoint3d(center.x,center.y - size/6),PyGePoint3d(center.x,center.y+size-size/10-size/40))
    h_sec.TrueColor = col_s
    h_sec.Lineweight = AcLineWeight.acLnWt030
    h_min = acad_model_space.AddLine(PyGePoint3d(center.x,center.y - size/6),PyGePoint3d(center.x,center.y+size-size/10-size/8))
    h_min.TrueColor = col_m
    h_min.Lineweight = AcLineWeight.acLnWt030
    h_hour = acad_model_space.AddLine(PyGePoint3d(center.x,center.y - size/6),PyGePoint3d(center.x,center.y+size-size/10-size/4))
    h_hour.TrueColor = col_h
    h_hour.Lineweight = AcLineWeight.acLnWt030
    for i in range(1,60):
        ang = ang_1_60*i
        line2 = line.Copy()
        line2.Rotate(center,ang)
        if not (i%5):
            spt = line2.StartPoint
            ept = line2.EndPoint
            line2.ScaleEntity(ept,1.5)
            line2.Lineweight = AcLineWeight.acLnWt050

            mat = PyGeMatrix3d.rotation(ang,PyGeVector3d.kZaxis,center)
            h2 = hour.Copy()
            h2.TextString = str(int(i/5))
            h2.TransformBy(mat)
            h2.Rotate(h2.InsertionPoint,-ang)


    line.ScaleEntity(line.EndPoint,1.5)
    line.Lineweight = AcLineWeight.acLnWt050
    acad_active_document.Regen(AcRegenType.acActiveViewport)
    from datetime import datetime
    mytime = datetime.now()
    my_h = mytime.hour
    my_m = mytime.minute
    my_s = mytime.second
    h_sec.Rotate(center,ang_1_60*my_s)
    h_min.Rotate(center,ang_1_60*my_m)
    h_hour.Rotate(center,ang_1_60*my_h*5+ang_1_60*(my_m // 12))
    seconds = 0
    while True:
        mytime = datetime.now()
        update = False
        if my_m != mytime.minute:
            h_min.Rotate(center,ang_1_60)
            my_m = mytime.minute
            if not (my_m % 12):
                h_hour.Rotate(center,ang_1_60)
            update = True
        if my_s != mytime.second:
            h_sec.Rotate(center,ang_1_60)
            my_s = mytime.second
            update = True
            seconds += 1
        if update:
            acad_active_document.Regen(AcRegenType.acActiveViewport)
            print(f"{my_h}:{my_m}:{my_s}")
        if seconds >= 3: break

def test_create(object_AcadCircle,
                object_Acad3DFace,
                object_AcadPolygonMesh,
                object_Acad3DPolyline,
                object_AddArc,
                object_AcadAttribute,
                object_AddMInsertBlock,
                ):
    objects = (object_AcadCircle,
                object_Acad3DFace,
                object_AcadPolygonMesh,
                object_Acad3DPolyline,
                object_AddArc,
                object_AcadAttribute,
                object_AddMInsertBlock
                )