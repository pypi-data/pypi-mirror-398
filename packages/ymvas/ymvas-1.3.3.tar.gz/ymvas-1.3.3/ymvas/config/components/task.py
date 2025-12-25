from __future__ import annotations

from functools import lru_cache
from os.path import basename
from ymvas.utils.errors import YException

class Task:

    def __init__(self, src: str|None = None) -> None:
        self.src   = src
        self._data = {}
    
    @property
    def data(self) -> dict:
        return self._data
    
    @property
    @lru_cache
    def name(self) -> str:
        if self.src is not None:
            return basename(self.src)

        if 'base' not in self.data:    
            raise YException('task-without-source')

        base = self.data['base']
        for i, c in enumerate( base ):
            if "]" == c:
                base = base[i+1:len(base)]
                break
        
        if len(base.strip("- ")) == "":
            base += "\n" + "\n".join(self.properties)
        
        return base
    
    @property
    def description(self) -> str:
        if self.src is not None:
            return self.name

        if "base" not in self.data:
            raise YException('task-without-source')
        
        base = self.data['base']
        for i, c in enumerate( base ):
            if "]" == c:
                base = base[i+1:len(base)]
                break
        
        if len(base.strip("- ")) == "":
            base += "\n" + "\n".join(self.properties)

        return base
    
    @property
    def is_root(self) -> bool:
        return self.src is not None

    @property
    def parent(self) -> None | Task:
        if 'parent' in self.data:
            return self.data['parent']
        return None

    @property
    @lru_cache
    def finished(self) -> bool:
        # base tasks are files 
        # and they are only finished when file is deleted
        if self.src is not None:
            return False

        if 'base' not in self.data:    
            raise YException('task-without-source')

        d = self.data['base'].strip()
        d = d.replace(' ','')
        d = d[:3].lower()
        return d == "[x]"
    
    @property
    def lines(self) -> list[str]:
        if 'lines' in self.data:
            return self.data['lines']

        if self.src is None:
            return []

        with open(self.src,'r') as f:
            lines = f.read().split('\n')
            self._data['lines'] = lines
            return lines

    @property
    @lru_cache
    def sections(self) -> list[Task]:
        taskr = []
        lines = [(i,line) for i,line in enumerate(self.lines)]
        def is_task(x):
            t = x.replace(' ','')
            if t == '':
                return False
            t = t[:3].lower()
            return t.startswith('[]') or t.startswith('[x]')

        tasks = [x for x in lines if is_task(x[1])]
        tasks = [(i[0],i[1].find('['), i[1]) for i in tasks]
        levls = list(set([i[1] for i in tasks]))
        
        if len( levls ) == 0:
            return []

        levl0 = [x for x in tasks if x[1] == levls[0]]
        maxln = lines[-1][0]
        maxts = len( levl0 )
        
        for i, t in enumerate( levl0 ):
            start, end = t[0], maxln
            if not ((i+1) >= maxts):
                end = levl0[i+1][0] - 1
            
            st = Task()

            st._data[  'lines'   ] = [l[1] for l in lines[start+1:end]]
            st._data[  'base'    ] = lines[start][1]
            st._data[  'parent'  ] = self
            st._data[ 'position' ] = ( start+1, end )

            taskr.append( st )

        return taskr
    

    @property
    @lru_cache
    def properties(self) -> list[str]:
        valid = []

        for line in self.lines:
            t = line.replace(' ','')
            t = t[:3].lower()
            if t.startswith('[]') or t.startswith('[x]'):
                break
            valid.append( line )

        return valid

    
    def __repr__(self) -> str:
        maxs = 35
        desc = self.description.lstrip(" ->")
        desc = desc[0:maxs-3] + '...' if len(desc) > maxs else desc
        return f"Task(is_root={self.is_root}, finished={self.finished}, description='{desc}')"
