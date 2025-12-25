
import os ,shutil
from os.path import dirname, join, exists
from ymvas.utils import walker

_dir = dirname(__file__)

class Creator:

    def __init__(self, init:str, target:str ):
        self._type  = init
        self.src    = join(_dir,init)
        self.target = target


    def local(self):
        _git = join(self.target, '.git')
        if not exists(_git):
            return

        ignore = join(_git, 'info', 'exclude')
        entry  = ".ymvas/"

        # file doesn't exist → create with entry
        if not exists(ignore):
            with open(ignore, "w") as f:
                f.write(entry + "\n")
            return

        # file exists → append only if entry missing
        with open(ignore, "r+") as f:
            content = f.read().splitlines()
            if entry not in content:
                f.write(entry + "\n")


    def run(self):
        if self._type == 'local':
            self.local()

        for f in walker(self.src):
            dest = f.replace(self.src,self.target)

            if exists(dest):
                continue

            dic = dirname(dest)
            os.makedirs(dic,exist_ok=True)
            shutil.copyfile(f, dest)
