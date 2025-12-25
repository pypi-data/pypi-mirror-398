from __future__ import annotations

from os.path import basename, exists, join
from ymvas.utils import get_yaml

# for types
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ymvas.settings import Settings



class YSettings:

    def __init__(self, settings:"Settings") -> None:
        self.settings = settings
        self._data    = get_yaml( settings.f_settings )

    
    @property
    def data(self) -> dict:
        return self._data
    
    

    # avatar info
    @property
    def is_avatar_simple(self):
        # avatar in settings can be setup with replative 
        # or absolute path so if it's not simple avatar
        # can be palced in any folder or path

        return not isinstance(
            self.data.get("avatar",None), 
            dict
        )

    @property
    def has_avatar(self) -> bool:
        avatar = self.avatar_fullpath
        if avatar is None:
            return False
        return exists(avatar)


    @property
    def avatar(self) -> str | None:
        avatar = self.data.get('avatar',None)
        
        if avatar is None:
            return None

        if isinstance(avatar,dict):
            avatar = avatar.get('src',None)
        
        if isinstance(avatar,str):
            return avatar
        
        return None

    @property
    def avatar_relpath(self) -> str | None:
        avatar = self.avatar
        if avatar is None:
            return None

        if self.is_avatar_simple:
            ph = join(self.settings.d_settings, avatar )
            return self.settings.relpath( ph )

        return avatar
    
    @property
    def avatar_fullpath(self) -> str | None:
        avatar = self.avatar_relpath
        if avatar is None:
            return None
        return join(self.settings.root, avatar)

    @property
    def avatar_basename(self) -> str | None:
        if self.avatar is None:
            return None
        else:
            return basename(self.avatar)
    
        
