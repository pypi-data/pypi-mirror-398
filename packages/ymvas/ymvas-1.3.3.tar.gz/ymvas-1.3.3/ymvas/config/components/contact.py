
from datetime import date
from functools import lru_cache
from os.path import basename, splitext

from dateutil import parser
from ymvas.utils.files import get_yaml
from ymvas.config.components.event import Event

class Contact:

    def __init__(self, src:str ):
        self.src   = src
        self._data = get_yaml(src)
        
    @property
    def data(self) -> dict:
        return self._data

    
    @property
    @lru_cache
    def file_name(self) -> str:
        return splitext(basename(self.src))[0].strip()
        
    @property
    @lru_cache
    def name(self) -> str:
        _name = self.data.get('name')

        if isinstance(_name,str):
            return _name
        
        return self.file_name

    @property
    @lru_cache
    def name_title(self) -> str:
        _name = self.data.get('name')
        if isinstance(_name,str):
            return _name

        _name = self.file_name
        _name = _name.replace("-"," ")
        _name = _name.replace("_"," ")

        return _name.title()


    # birthday info
    @property
    @lru_cache
    def has_birthday(self) -> bool:
        if not "birthday" in self.data:
            return False
        
        if self.birthday is None:
            return False
        
        return True

    
    @property
    @lru_cache
    def birthday(self) -> date | None:

        birthday = self.data.get("birthday")
        if birthday is None:
            return

        if isinstance(birthday,str):
            try:
                return parser.parse( birthday ).date()
            except Exception:
                return None

        return None
    
    @property
    @lru_cache
    def birthday_date_str(self) -> str | None:
        if self.birthday is None:
            return None

        return self.birthday.strftime("%Y-%m-%d")
    
    @property
    @lru_cache
    def birthday_date_cron_str(self) -> str | None:
        bdt = self.birthday
        if bdt is None:
            return
        
        return f"0 0 {bdt.day} {bdt.month} *"

    
    def get_birthday_event(self) -> Event | None:
        if not self.birthday:
            return None

        e = Event()
        e.src = self.src
        e._data = {
            "active" : True,
            "is-all-day" : True,
            "start" : self.birthday,
            "frequency": "YEARLY",
            "by-month" : self.birthday.month,
            "by-month-day" : self.birthday.day,
            "name" : self.name_title
        }

        return e
                






