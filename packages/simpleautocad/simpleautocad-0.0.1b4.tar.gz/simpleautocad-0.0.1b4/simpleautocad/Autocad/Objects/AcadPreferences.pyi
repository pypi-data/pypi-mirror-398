from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadPreferences(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    Display: AcadPreferencesDisplay
    Drafting: AcadPreferencesDrafting
    Files: AcadPreferencesFiles
    OpenSave: AcadPreferencesOpenSave
    Output: AcadPreferencesOutput
    Profiles: AcadPreferencesProfiles
    Selection: AcadPreferencesSelection
    System: AcadPreferencesSystem
    User: AcadPreferencesUser
