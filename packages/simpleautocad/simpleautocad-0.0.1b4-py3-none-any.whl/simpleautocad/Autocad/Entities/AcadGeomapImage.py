from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadRasterImage import AcadRasterImage



class AcadGeomapImage(AcadRasterImage):
    def __init__(self, obj) -> None: super().__init__(obj)

    GeoImageBrightness: int = proxy_property(int,'GeoImageBrightness',AccessMode.ReadWrite)
    GeoImageContrast: int = proxy_property(int,'GeoImageContrast',AccessMode.ReadWrite)
    GeoImageFade: int = proxy_property(int,'GeoImageFade',AccessMode.ReadWrite)
    GeoImageHeight: float = proxy_property(float,'GeoImageHeight',AccessMode.ReadOnly)
    GeoImageWidth: float = proxy_property(float,'GeoImageWidth',AccessMode.ReadOnly)

    def Copy(self) -> AcadGeomapImage:
        return AcadGeomapImage(self._obj.Copy())
