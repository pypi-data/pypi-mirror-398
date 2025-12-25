from __future__ import annotations

from functools import lru_cache
from os.path import join
from ymvas.config.components.endpoint import Endpoint
from ymvas.utils import get_yaml, walker

# for types
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ymvas.settings import Settings

class YEndpointsSettings:

    def __init__(self, settings:"Settings") -> None:
        self.settings = settings
        self._data    = get_yaml( settings.f_settings_endpoints )
        
    @property
    def data(self) -> dict:
        return self._data

    @property
    @lru_cache
    def configured_files(self) -> list[dict[str,str|dict]] | None:
        settings = self.settings
        data = self.data
        def _get_files (_files ) -> list[dict[str,str|dict]]:
            nonlocal settings
            if isinstance(_files,dict):
                return list(
                    {
                        "fullpath" : join(settings.d_endpoints,k),
                        "relpath"  : k,
                        "conf" : v
                    } for k,v in _files.items()
                )
            elif isinstance(_files,list):
                return list({
                    "fullpath" : join(settings.d_endpoints,f['path']),
                    "relpath"  : f['path'],
                    "conf" : f
                } for f in _files if 'path' in f)
            return []

        if 'files' in data:
            files = _get_files(data['files'])
            if len(files) == 0:
                return None
            return files

        files = _get_files(data)
        if len(files) == 0:
            return None
        return files
    
    @property
    @lru_cache
    def endpoints(self) -> list[Endpoint]:
        endpoints  = []
        settings   = self.settings
        configured = self.configured_files

        for f in walker(settings.d_endpoints):
            conf = {}

            if not ( configured is None ):
                for t in configured:
                    if t['fullpath'] != f:
                        continue
                
                    _conf = t.get('conf',{})
                    if not isinstance(_conf,dict):
                        continue
                    conf = _conf

            e = Endpoint( f, conf )
            endpoints.append(e)

        return endpoints
