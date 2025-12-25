from win32com.client import GetActiveObject as AppAttach, Dispatch as AppCreate, CDispatch
from winreg import CloseKey, OpenKey, QueryValueEx, HKEY_CLASSES_ROOT
from pythoncom import CoInitialize, CoUninitialize, CoCreateInstance, CLSCTX_LOCAL_SERVER, IID_IDispatch, com_error
from abc import ABC, abstractmethod

def com_server_is_running(prog_id: str):
    try:
        return AppAttach(prog_id)
    except com_error as e:
        return False
        raise com_error(e)

def get_clsid(cls):
    if cls.__app_version__:
        curver = f'{cls.__app_name__}.Application.{cls.__app_version__}'
        registry_path_clsid = r"{}\CLSID".format(curver)
    else:
        registry_path_clsid = r"{}.Application\CLSID".format(cls.__app_name__)
        registry_path_curver = r"{}.Application\CurVer".format(cls.__app_name__)
    try:
        key = OpenKey(HKEY_CLASSES_ROOT, registry_path_clsid)
        clsid = QueryValueEx(key, None)[0]
        CloseKey(key)
        if not cls.__app_version__:
            key = OpenKey(HKEY_CLASSES_ROOT, registry_path_curver)
            curver = QueryValueEx(key, None)[0]
            CloseKey(key)
            try:
                cls.__app_version__ = str(curver).split('.')[2]
            except: pass
        return clsid, curver
    except FileNotFoundError:
        raise FileNotFoundError(f"Ключ реестра '{registry_path_clsid}' не найден. Приложение не установлено или COM не зарегистрирован.")
    except Exception as e:
        raise Exception(f"Произошла ошибка при чтении реестра: {e}")

def create_new_instance_explicitly(clsid):
    try:
        obj = CoCreateInstance(
            clsid,
            None,
            CLSCTX_LOCAL_SERVER,
            IID_IDispatch
        )
        app = AppCreate(obj)
        return app
    except com_error as e:
        raise com_error(f"Ошибка COM при создании экземпляра приложения: {e}")

class AppObject:
    def __init__(self, obj):
        if not isinstance(obj,CDispatch): 
            obj = obj._obj
        self._obj = obj
    def __repr__(self):
        return self._obj.__class__
    def __str__(self):
        return f'{self._obj}'
    def __getattr__(self, name):
        return getattr(self._obj,name)
    def __call__(self):
        return self._obj

class Application(ABC):
    def __new__(cls, dispatch_object=None):
        instance = super().__new__(cls)
        instance._dispatch_obj_to_init = None 
        instance._is_owner = False
        instance.__app_clsid__ = None
        instance.__app_full_name__ = None
        # Логика определения типа подключения
        if dispatch_object is not None:
            instance._dispatch_obj_to_init = dispatch_object
        else:
            try:
                instance._dispatch_obj_to_init = instance._manage_application_instance()
            except Exception as e:
                Exception(f"Ошибка запуска приложения: {e}")
        return instance
    
    def __init__(self, dispatch_object=None):
        super().__init__(self._dispatch_obj_to_init)
        del self._dispatch_obj_to_init # Очищаем временное хранилище

    @abstractmethod
    def _manage_application_instance(self): pass
    


class AppObjectCollection(AppObject):
    def __init__(self, obj):
        super().__init__(obj)

    @property
    def Count(self) -> int: 
        return self._obj.Count

    def Item(self, Index: int|str) -> AppObject:
        return AppObject(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AppObject(item)
            yield obj

def clear_com_cache():
    import win32com.client.gencache
    import os
    import shutil
    gentype_path = win32com.client.gencache.GetGeneratePath()
    if os.path.exists(gentype_path):
        # logger.debug(f"Удаление кэша COM: {gentype_path}")
        try:
            shutil.rmtree(gentype_path)
            # logger.debug("Кэш успешно удален.")
        except OSError as e:
            raise com_error(f"Ошибка при удалении кэша: {e}. Закройте приложение COM-сервер и повторите попытку.")
    else:
        pass
        # logger.debug("Папка кэша gen_py не найдена. Возможно, кэш еще не был создан.")