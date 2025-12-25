from fnmatch import fnmatch
from functools import lru_cache
from os.path import splitext, basename
from pathlib import Path
from typing import TYPE_CHECKING

from ymvas.utils.files import get_yaml, walker
if TYPE_CHECKING:
    from ymvas.settings import Settings


class YCommandsSettings:
      
    VALID_EXECUTORS = [
        {"ext" : 'py'   , "run" : "python3" },
        {"ext" : 'bash' , "run" : "bash"    },
        {"ext" : 'sh'   , "run" : "sh"      }
    ]

    def __init__(self, settings:"Settings") -> None:
        self.settings = settings
        self._data = get_yaml(settings.f_settings_commands)
    
    @property
    def data(self) -> dict:
        return self._data

    @property
    @lru_cache
    def ignore_dot_files(self) -> bool:
        if 'ignore-dot-files' not in self.data:
            return True
        
        i = self.data['ignore-dot-files']
        if isinstance(i,str):
            return i.strip().lower() == 'true'

        if isinstance(i,bool):
            return i

        if isinstance(i,int):
            return i == 1

        return True
    
    @property
    @lru_cache
    def ignored(self) -> list[str]:
        if 'ignore' not in self.data:
            return []

        i = self.data['ignore']

        if isinstance(i,str):
            return [i]

        if isinstance(i,list):
            return [ x for x in i if isinstance(x,str) ]

        return []
    
    @property
    @lru_cache
    def descriptions(self) -> dict[str,str]:
        if 'descriptions' not in self.data:
            return {}
        
        descs = self.data['descriptions']
        if not isinstance(descs,dict):
            return {}
        
        descs = {k:str(v) for k,v in descs.items()}
        return descs
        

    
    def list(self) -> list:
        settings = self.settings
        descrips = self.descriptions

        vdict = {x['ext']:x['run'] for x in self.VALID_EXECUTORS}
        
        def is_ignored(item):
            return any(fnmatch(item,pat) for pat in self.ignored)

        cmds = []
        for ab in walker(settings.d_commands):
            fl = str(Path(ab).relative_to(settings.d_commands))
            st = splitext(fl)
            rn = vdict.get(st[1].strip('.'),None)

            if rn is None:
                continue

            cmd = st[0]

            f = basename(cmd)
            if f.startswith('.') and self.ignore_dot_files:
                continue

            if is_ignored(cmd):
                continue
            
            cmds.append({
                "cmd"  : cmd,
                "run"  : rn,
                "path" : ab,
                "desc" : descrips.get(cmd,None)
            })

        return cmds
