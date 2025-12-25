from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *

class AcadPreferences(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Display: AcadPreferencesDisplay = proxy_property('AcadPreferencesDisplay','Display',AccessMode.ReadOnly)
    Drafting: AcadPreferencesDrafting = proxy_property('AcadPreferencesDrafting','Drafting',AccessMode.ReadOnly)
    Files: AcadPreferencesFiles = proxy_property('AcadPreferencesFiles','Files',AccessMode.ReadOnly)
    OpenSave: AcadPreferencesOpenSave = proxy_property('AcadPreferencesOpenSave','OpenSave',AccessMode.ReadOnly)
    Output: AcadPreferencesOutput = proxy_property('AcadPreferencesOutput','Output',AccessMode.ReadOnly)
    Profiles: AcadPreferencesProfiles = proxy_property('AcadPreferencesProfiles','Profiles',AccessMode.ReadOnly)
    Selection: AcadPreferencesSelection = proxy_property('AcadPreferencesSelection','Selection',AccessMode.ReadOnly)
    System: AcadPreferencesSystem = proxy_property('AcadPreferencesSystem','System',AccessMode.ReadOnly)
    User: AcadPreferencesUser = proxy_property('AcadPreferencesUser','User',AccessMode.ReadOnly)