import json, sys
from os.path import join, exists
from functools import lru_cache

class Gits:
    _separator_start = "# ymvas [start] don't change this line"
    _separator_end   = "# ymvas [end] don't change this line"

    def __init__(self, stg):
        self.stg = stg

        # skip server side, non repo and non ymvas
        if stg.is_server     or \
           not stg.is_repo   or \
           not stg.is_ymvas:
            return

        self._conf_file = join(stg.hooks,'ymvas.json')
        self._check_hocks()

    def _check_hocks(self):
        stg = self.stg

        conf = self._get_ymvas_hooks()
        self._new_hock_conf()

        from ..__init__ import __version__
        if conf.get('version') != __version__:
            self._new_hock_conf()
            return


    @lru_cache(maxsize=None)
    def _get_ymvas_hooks(self):
        try:
            with open(self._conf_file,'r') as f:
                data = json.loads(f.read())
                if not isinstance(data,dict):
                    return {}
                return data
        except Exception:
            return {}

    def _new_hock_conf(self):
        hook = join(self.stg.hooks,'pre-commit' )

        content = ""
        if exists(hook):
            with open(hook,'r') as f:
                content = f.read()

        skip = False
        ncontent = []
        for l in content.split("\n"):
            if self._separator_end in l:
                skip = False
                continue
            if skip:
                continue
            if self._separator_start in l:
                skip = True
                continue
            ncontent.append(l)

        root = "$(git rev-parse --show-toplevel)"
        ncontent = [
            "#!/bin/sh",
            self._separator_start,
            f"{sys.executable} -m ymvas trigger pre-commit --src=\"{root}\" ",
            self._separator_end,
        ] + ncontent[1:]

        with open(hook,'w') as f:
            f.write("\n".join(ncontent))

        # sys.executable
        with open(self._conf_file,'w') as fs:
            from ..__init__ import __version__

            data = {
                "version" : __version__ ,
            }

            fs.write(json.dumps(data, indent= 10))

    def pull(self):
        pass
