from ..Base import *
from ..Proxy import *
from .AcadRasterImage import AcadRasterImage as AcadRasterImage

class AcadGeomapImage(AcadRasterImage):
    def __init__(self, obj) -> None: ...
    GeoImageBrightness: int
    GeoImageContrast: int
    GeoImageFade: int
    GeoImageHeight: float
    GeoImageWidth: float
    def Copy(self) -> AcadGeomapImage: ...
