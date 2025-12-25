from __future__ import annotations

from functools import lru_cache
from os.path import exists
from ymvas.utils import get_yaml

# for types
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ymvas.settings import Settings

class YEventsSettings:

    def __init__(self, settings: Settings ) -> None:
        self.settings = settings
        self._data    = get_yaml( settings.f_settings_events )
    
    @property
    def data(self) -> dict:
        return self._data


    # CALENDAR SETTINGS
    @property
    @lru_cache
    def calendar_create(self) -> bool:
        settings = self.settings
        if not exists(settings.f_settings_events):
            return False

        # by default we don't create calendar for submodules
        # only for main repos
        if settings.is_main:
            _compile = True

            if 'compile' in self.data:
                _compile = str(self.data['compile']).lower() == 'true'
            
            return _compile
        

        if 'compile' in self.data:
            return str(self.data["compile"]).lower() == "true"
        
        return False


    @property
    @lru_cache
    def calendar_submodules(self) -> list[Settings]:
        settings = self.settings

        if not settings.is_main:
            # submodules do not use submodules
            return []

        cnf = self.data
        
        if not 'modules' in cnf:
            return []
        
        modules = cnf["modules"]
        
        if isinstance(modules, list):
            mnames   = [m for m in modules if isinstance(m,str)]
            smodules = settings.modules

            return [
                m for m in smodules.values() if m.alias in mnames \
                and not m.root
            ]

        elif isinstance(modules,str):
            attr = modules.lower()
            if attr == "*" or attr == "all":
                return [
                    m for m in settings.modules.values() \
                    if not m.is_main
                ]

        return []
    
    @property
    def calendar_adds_birthdays(self) -> bool:
        data = self.data

        if not 'contacts' in data:
            return False
        
        contacts = self.data["contacts"]

        if isinstance(contacts,str):
            return contacts.lower() == 'all' or contacts.lower() == "*"

        # TODO make it posble so we can filter contacts

        return False
    
    def calendar_adds_tasks(self) -> bool:
        # TODO
        return False

            
        
        
    


