import pytest
import time
import math
from typing import Generator
from simpleautocad import *
# import pandas as pd
from colorama import init, Fore, Back, Style
init(autoreset=True)

OFFSET_DIR:PyGeVector3d = PyGeVector3d.kXaxis
OFFSET_COUNT:int = 0
OFFSET_DIST_X:int = 100
OFFSET_DIST_Y:int = 100
OFFSET_DIST_Z:int = 0

def init_point():
    global OFFSET_COUNT, OFFSET_DIR, OFFSET_DIST_X, OFFSET_DIST_Y, OFFSET_DIST_Z
    init_pt = PyGePoint3d(OFFSET_COUNT*OFFSET_DIR.x*OFFSET_DIST_X)
    OFFSET_COUNT += 1
    return init_pt

@pytest.fixture(scope="session")
def acad_app() -> Generator[AutoCAD,None,None]:
    # if com_server_is_running(GetProgID(AcadApplication)):
    #     pytest.exit("Перед запуском теста необходимо закрыть AutoCAD")
    print("\n--- Продключение к AutoCAD.Application ---")
    try:
        acad = AutoCAD()
    except Exception as e:
        pytest.fail(f"Не удалось запустить AutoCAD: {e}")
    # Ожидание загрузки
    # _ = acad.VBE.MainWindow.Visible
    # timeout = 20
    # start_time = time.time()
    # while time.time() - start_time < timeout:
    #     try:
    #         # Попытка доступа к свойству, которое требует полной инициализации
    #         print(".")
    #         _ = acad.VBE.MainWindow.Visible 
    #         print("\nAutoCAD готов к работе.")
    #         break
    #     except pythoncom.com_error:
    #         # Пока не готов, ждем
    #         time.sleep(0.2)
    #         # print("\n\tПродключение к AutoCAD.Application .",end=" ")
    # else:
    #     pytest.fail("Время ожидания запуска AutoCAD истекло.")
    time.sleep(1.2)
    acad.Visible = True
    yield acad
    # acad.Visible = True
    # time.sleep(0.2)
    # acad.ActiveDocument.Regen(AcRegenType.acAllViewports)
    # acad.ZoomAll()
    # time.sleep(5)
    # print(f"Сохранение документа...")
    # acad.ActiveDocument.SaveAs(r'Y:\simpleautocad_test.dwg',AcSaveAsType.ac2007_dwg)
    # acad.Quit() # Закомментировать, чтобы окно не закрывалось сразу после тестов
    print("\n--- Отключение AutoCAD.Application ---")
    del acad

@pytest.fixture(scope="function")
def acad_active_document(acad_app:AutoCAD) -> Generator[AcadDocument,None,None]:
    time.sleep(0.2)
    doc = acad_app.ActiveDocument
    assert doc.__class__ == AcadDocument
    yield doc

@pytest.fixture(scope="function")
def acad_model_space(acad_active_document:AcadDocument) -> Generator[AcadModelSpace,None,None]:
    # Убедимся, что мы в ModelSpace
    acad_active_document.ActiveSpace = AcActiveSpace.acModelSpace
    ms = acad_active_document.ModelSpace
    assert ms.__class__ == AcadModelSpace
    yield ms
    # Очистка чертежа после каждого теста
    objects_to_delete = [obj for obj in ms]
    for obj in objects_to_delete:
        obj.Delete()
    acad_active_document.Regen(AcRegenType.acAllViewports)
    print("--- Очистка ModelSpace после теста ---")

@pytest.fixture(scope="function")
def object_AcadCircle(acad_model_space:AcadModelSpace) -> Generator[AcadCircle,None,None]:
    print('\n')
    object_class = AcadCircle
    pt = init_point()
    pt[0]+=10
    Center = PyGePoint3d(pt.x + OFFSET_DIST_X / 2, pt.y + OFFSET_DIST_Y / 2, pt.z + OFFSET_DIST_Z / 2)
    Radius = OFFSET_DIST_X / 2 - 10
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}Center{Fore.WHITE} = {Center.__class__.__name__}({Center})\n\
{Fore.CYAN}Radius{Fore.WHITE} = {Radius.__class__.__name__}({Radius})\n\
"
    print(prompt)
    obj = acad_model_space.AddCircle(Center, Radius)
    assert obj.__class__ is object_class
    print(f"{obj} {obj.__class__.__name__} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()

@pytest.fixture(scope="function")
def object_Acad3DFace(acad_model_space:AcadModelSpace) -> Generator[Acad3DFace,None,None]:
    print('\n')
    object_class = Acad3DFace
    pt = init_point()
    pt[0]+=10
    Point1 = PyGePoint3d(5 + pt.x,5+pt.y,pt.z)
    Point2 = PyGePoint3d(pt.x+OFFSET_DIST_X-5,pt.y+5,pt.z)
    Point3 = PyGePoint3d(pt.x+OFFSET_DIST_X-5,pt.y+OFFSET_DIST_Y-5,pt.z)
    Point4 = PyGePoint3d(pt.x+5,pt.y+OFFSET_DIST_Y-5,pt.z)
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}Point1{Fore.WHITE} = {Point1.__class__.__name__}({Point1})\n\
{Fore.CYAN}Point2{Fore.WHITE} = {Point2.__class__.__name__}({Point2})\n\
{Fore.CYAN}Point3{Fore.WHITE} = {Point3.__class__.__name__}({Point3})\n\
{Fore.CYAN}Point4{Fore.WHITE} = {Point4.__class__.__name__}({Point4})\n\
"
    print(prompt)
    obj = acad_model_space.Add3DFace(Point1, Point2, Point3, Point4)
    assert obj.__class__ is object_class
    print(f"{obj} {obj.__class__.__name__} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()
    
@pytest.fixture(scope="function")
def object_AcadPolygonMesh(acad_model_space:AcadModelSpace) -> Generator[AcadPolygonMesh,None,None]:
    print('\n')
    object_class = AcadPolygonMesh
    pt = init_point()
    pt[0]+=10
    M = 4
    N = 4
    PoinsMatrix = vDoubleArray(
        [pt.x,0,0,                       pt.x+OFFSET_DIST_X/4,0,10,                       pt.x+OFFSET_DIST_X/2,0,0,                       pt.x+OFFSET_DIST_X,0,1,
        pt.x,pt.y+OFFSET_DIST_Y/4,0,    pt.x+OFFSET_DIST_X/4,pt.y+OFFSET_DIST_Y/4,10,    pt.x+OFFSET_DIST_X/2,pt.y+OFFSET_DIST_Y/4,0,    pt.x+OFFSET_DIST_X,pt.y+OFFSET_DIST_Y/4,10,
        pt.x,pt.y+OFFSET_DIST_Y/2,0,    pt.x+OFFSET_DIST_X/4,pt.y+OFFSET_DIST_Y/2,-10,    pt.x+OFFSET_DIST_X/2,pt.y+OFFSET_DIST_Y/2,0,    pt.x+OFFSET_DIST_X,pt.y+OFFSET_DIST_Y/2,0,
        pt.x,pt.y+OFFSET_DIST_Y,0,      pt.x+OFFSET_DIST_X/4,pt.y+OFFSET_DIST_Y,10,      pt.x+OFFSET_DIST_X/2,pt.y+OFFSET_DIST_Y,0,      pt.x+3*OFFSET_DIST_X/4,pt.y+3*OFFSET_DIST_Y/4,0],
        check_count=M*N*3
    )
    
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}M{Fore.WHITE} = {M.__class__.__name__}({M})\n\
{Fore.CYAN}N{Fore.WHITE} = {N.__class__.__name__}({N})\n\
{Fore.CYAN}PointsMatrix{Fore.WHITE} = {PoinsMatrix.__class__.__name__}({PoinsMatrix})\n\
"
    print(prompt)
    obj = acad_model_space.Add3DMesh(M,N,PoinsMatrix)
    assert obj.__class__ is object_class
    print(f"{object_class} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()
    
@pytest.fixture(scope="function")
def object_Acad3DPolyline(acad_model_space:AcadModelSpace) -> Generator[Acad3DPolyline,None,None]:
    print('\n')
    object_class = Acad3DPolyline
    pt = init_point()
    pt[0]+=10
    PointsArray = PyGePoint3dArray(0,0,0,10,10,10,15,-15,15,13,5,-4)
    
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}PointsArray{Fore.WHITE} = {PointsArray.__class__.__name__}({PointsArray})\n"
    print(prompt)
    obj = acad_model_space.Add3DPoly(PointsArray)
    assert obj.__class__ is object_class
    print(f"{object_class} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()
    
@pytest.fixture(scope="function")
def object_AddArc(acad_model_space:AcadModelSpace) -> Generator[AcadArc,None,None]:
    print('\n')
    object_class = AcadArc
    pt = init_point()
    pt[0]+=10
    Center = PyGePoint3d(pt.x + OFFSET_DIST_X / 2, pt.y + OFFSET_DIST_Y / 2, pt.z + OFFSET_DIST_Z / 2)
    Radius = OFFSET_DIST_X / 2 - 10
    StartAngle = math.pi / 2
    EndAngle = math.pi * 2
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}Center{Fore.WHITE} = {Center.__class__.__name__}({Center})\n\
{Fore.CYAN}Radius{Fore.WHITE} = {Radius.__class__.__name__}({Radius})\n\
{Fore.CYAN}StartAngle{Fore.WHITE} = {StartAngle.__class__.__name__}({StartAngle})\n\
{Fore.CYAN}EndAngle{Fore.WHITE} = {EndAngle.__class__.__name__}({EndAngle})\n\
"
    print(prompt)
    obj = acad_model_space.AddArc(Center, Radius, StartAngle, EndAngle)
    assert obj.__class__ is object_class
    print(f"{object_class} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()
    
@pytest.fixture(scope="function")
def object_AcadAttribute(acad_model_space:AcadModelSpace) -> Generator[AcadAttribute,None,None]:
    print('\n')
    object_class = AcadAttribute
    pt = init_point()
    pt[0]+=10
    Height = 10
    Mode = AcAttributeMode.acAttributeModeMultipleLine
    Prompt = 'Описание атрибута'
    InsertionPoint = PyGePoint3d(pt.x+OFFSET_DIST_X/2,pt.y+OFFSET_DIST_Y/2,pt.z+OFFSET_DIST_Z/2)
    Tag = '_ТЕГ_'
    Value = 'Значение'
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}Height{Fore.WHITE} = {Height.__class__.__name__}({Height})\n\
{Fore.CYAN}Mode{Fore.WHITE} = {Mode.__class__.__name__}({Mode})\n\
{Fore.CYAN}Prompt{Fore.WHITE} = {Prompt.__class__.__name__}({Prompt})\n\
{Fore.CYAN}InsertionPoint{Fore.WHITE} = {InsertionPoint.__class__.__name__}({InsertionPoint})\n\
{Fore.CYAN}Tag{Fore.WHITE} = {Fore.CYAN}{Tag.__class__.__name__}{Fore.WHITE}({Tag})\n\
{Fore.CYAN}Value{Fore.WHITE} = {Value.__class__.__name__}{Fore.WHITE}({Value})\n\
"
    print(prompt)
    obj = acad_model_space.AddAttribute(Height,Mode,Prompt,InsertionPoint,Tag,Value)
    assert obj.__class__ is object_class
    print(f"{object_class} добавлен в {acad_model_space.Name}")
    yield obj
    # print(f'\nУдаление {obj}')
    # obj.Delete()

@pytest.fixture(scope="function")
def object_AddMInsertBlock(acad_model_space:AcadModelSpace) -> Generator[AcadBlock,None,None]:
    bl = acad_model_space.Document.Database.Blocks.Add(PyGePoint3d(),'TestBlock')
    bl.AddArc(PyGePoint3d(),15,math.pi,math.pi/3)
    print('\n')
    object_class = AcadMInsertBlock
    pt = init_point()
    pt[0]+=10
    InsertionPoint = pt
    Name = 'TestBlock'
    XScale= 1.0
    YScale= 1.2 
    ZScale= 1.4
    Rotation= math.pi/2
    NumRows= 2
    NumColumns= 3
    RowSpacing= 10.10
    ColumnSpacing = 20.20
    Password= vObjectEmpty
    prompt = f"Установка свойств {object_class}\n\
{Fore.CYAN}InsertionPoint{Fore.WHITE:<30} = {Fore.CYAN}{InsertionPoint.__class__.__name__}{Fore.WHITE}({InsertionPoint})\n\
{Fore.CYAN}Name{Fore.WHITE:<30} = {Fore.CYAN}{Name.__class__.__name__}{Fore.WHITE}({Name})\n\
{Fore.CYAN}XScale{Fore.WHITE:<30} = {Fore.CYAN}{XScale.__class__.__name__}{Fore.WHITE}({XScale})\n\
{Fore.CYAN}YScale{Fore.WHITE:<30} = {Fore.CYAN}{YScale.__class__.__name__}{Fore.WHITE}({YScale})\n\
{Fore.CYAN}ZScale{Fore.WHITE:<30} = {Fore.CYAN}{ZScale.__class__.__name__}{Fore.WHITE}({ZScale})\n\
{Fore.CYAN}Rotation{Fore.WHITE:<30} = {Fore.CYAN}{Rotation.__class__.__name__}{Fore.WHITE}({Rotation})\n\
{Fore.CYAN}NumRows{Fore.WHITE:<30} = {Fore.CYAN}{NumRows.__class__.__name__}{Fore.WHITE}({NumRows})\n\
{Fore.CYAN}NumColumns{Fore.WHITE:<30} = {Fore.CYAN}{NumColumns.__class__.__name__}{Fore.WHITE}({NumColumns})\n\
{Fore.CYAN}RowSpacing{Fore.WHITE:<30} = {Fore.CYAN}{RowSpacing.__class__.__name__}{Fore.WHITE}({RowSpacing})\n\
{Fore.CYAN}ColumnSpacing{Fore.WHITE:<30} = {Fore.CYAN}{ColumnSpacing.__class__.__name__}{Fore.WHITE}({ColumnSpacing})\n\
{Fore.CYAN}Password{Fore.WHITE:<30} = {Fore.CYAN}{Password.__class__.__name__}{Fore.WHITE}({Password})\n\
"
    print(prompt)
    obj = acad_model_space.AddMInsertBlock(InsertionPoint,Name,XScale,YScale,ZScale,Rotation,NumRows,NumColumns,RowSpacing,ColumnSpacing,Password)
    assert obj.__class__ == object_class
    print(f"{obj} {obj.__class__.__name__} добавлен в {acad_model_space.Name}")
    yield obj
    print(f'\nУдаление {obj}')
    # obj.Delete()