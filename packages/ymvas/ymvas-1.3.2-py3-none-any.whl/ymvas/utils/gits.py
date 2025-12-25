from os.path import exists, join
from pathlib import Path
from .files import climber


def find_root(src:str) -> tuple[str,bool]:
    def _git_bash_fix(p:str) -> str:
        dr = Path(p)
        if str(dr).startswith("/c/") or str(dr).startswith("\\c\\"):
            dr = Path("C:" + str(dr)[2:])
        return str(dr)

    for c in climber(src):
        ymf = join(c,".ymvas")
        git = join(c,".git")

        if not exists(ymf) and exists(git):
            return _git_bash_fix(c), False
        
        if exists(ymf):
            return _git_bash_fix(c), True

    return _git_bash_fix(src), False


